import base64
import re
from asyncio import Task, create_task, gather, get_event_loop
from datetime import datetime
from traceback import format_exc, format_exception
from typing import Any, Awaitable, Callable, Coroutine, Literal, Optional, TypeVar, cast
from uuid import uuid4

from aiofiles import open
from pydantic import BaseModel
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import (
    SQLModel,
    col,
    delete,
    desc,
    select,
)

from .ai import (
    P1Response,
    P1ReviewResponse,
    P2Response,
    P3Response,
    ReviewResponse,
    generate_image,
    generate_topic,
    review_p1 as ai_review_p1,
    review_p2_3 as ai_review_p2_3,
    summary_review_p1,
)
from .env import DB_URL
from .exception import (
    ModelFailure,
    QuestionNotFound,
    ReviewNotFound,
    SubmissionNotFound,
    TopicNotFound,
)
from .task import add_task
from .typing import (
    Answer,
    AnswerReview,
    OverallReview,
    Question,
    Review,
    Session,
    SlicedAnswer,
    SlicedAnswerReview,
    SlicedOverallReview,
    SlicedReview,
    SlicedSubmission,
    SlicedTopic,
    SlicedTopicQuestion,
    Statistics,
    Status,
    Submission,
    Topic,
    TopicPart,
)

engine = create_async_engine(DB_URL)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


T = TypeVar("T")


async def create_session_and_run(
    func: Callable[[AsyncSession], Awaitable[T]],
    _session: Optional[AsyncSession] = None,
) -> T:
    if _session:
        return await func(_session)
    else:
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as _session:
            return await func(_session)


async def get_session():
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


"""
Formater
"""


def format_topic(topic: Topic):
    return SlicedTopic(
        id=topic.id,
        color=topic.color,
        status=topic.status,
        type=topic.type,
        part=topic.part,
        summary=topic.summary,
        questions=[format_topic_question(question) for question in topic.questions]
        if topic.questions
        else None,
        submissions=[format_submission(sub) for sub in topic.submissions],
        reviews=[format_review(review) for review in topic.reviews],
        created_at=topic.created_at,
    )


def format_topic_question(question: Question):
    return SlicedTopicQuestion(
        id=question.id,
        topic_id=question.topic_id,
        question=question.question,
        artist_prompt=question.artist_prompt,
        file=question.file,
        keywords=question.keywords,
        created_at=question.created_at,
    )


def format_answer(answer: Answer):
    return SlicedAnswer(
        id=answer.id,
        question_id=answer.question_id,
        submission_id=answer.submission_id,
        content=answer.content,
        created_at=answer.created_at,
    )


def format_submission(submission: Submission):
    return SlicedSubmission(
        id=submission.id,
        topic_id=submission.topic_id,
        answers=[format_answer(answer) for answer in submission.answers],
        review=format_review(submission.review) if submission.review else None,
        created_at=submission.created_at,
    )


def format_review(review: Review):
    return SlicedReview(
        id=review.id,
        topic_id=review.topic_id,
        status=review.status,
        overall=format_overall_review(review.overall) if review.overall else None,
        answers=[format_question_review(q) for q in review.answers]
        if review.answers
        else [],
        created_at=review.created_at,
    )


def format_overall_review(overall: OverallReview):
    return SlicedOverallReview(
        id=overall.id,
        review_id=overall.review_id,
        score_range=overall.score_range,
        level_achieved=overall.level_achieved,
        overall_feedback=overall.overall_feedback,
        summary_feedback=overall.summary_feedback,
        detail_score=overall.detail_score,
        annotations=overall.annotations,
        improvement_suggestions=overall.improvement_suggestions,
    )


def format_question_review(question_review: AnswerReview):
    return SlicedAnswerReview(
        id=question_review.id,
        review_id=question_review.review_id,
        answer_id=question_review.answer_id,
        overall_score=question_review.overall_score,
        details=question_review.detail_score,
        feedback=question_review.feedback,
        annotations=question_review.annotations,
    )


"""
TOPIC
"""


async def get_topics(all: bool = False, _session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        statement = select(Topic).order_by(desc(Topic.created_at))
        if not all:
            statement = statement.where(Topic.status == Status.done)
        topics = list((await session.execute(statement)).scalars().all())
        return [format_topic(topic) for topic in topics]

    return await create_session_and_run(_inner, _session)


async def _get_topic(id: str, _session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        statement = select(Topic).where(Topic.id == id).order_by(desc(Topic.created_at))
        topic = (await session.execute(statement)).scalar()
        if not topic:
            raise TopicNotFound(id)

        return topic

    return await create_session_and_run(_inner, _session)


async def get_topic(id: str, _session: Optional[AsyncSession] = None):
    topic = await _get_topic(id, _session)
    return format_topic(topic)


async def _get_question(id, _session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        statement = select(Question).where(Question.id == id)
        question = (await session.execute(statement)).scalar()
        if question is None:
            raise QuestionNotFound()
        return question

    return await create_session_and_run(_inner, _session)


class CombinedP1Response(BaseModel):
    keywords: tuple[str, str]
    artist_prompt: str
    image_url: str


BASE64_IMAGE_REGEX = re.compile(r"^data:image\/([a-z]+);base64,(.+)")


async def _create_question_p1():
    prompt_response = cast(P1Response, await generate_topic("1"))
    if prompt_response is None:
        raise RuntimeError("can't generate prompt for image generation")

    image_url = await generate_image(prompt=prompt_response.artist_prompt)
    if image_url is None:
        raise RuntimeError("can't generate image")

    return CombinedP1Response(
        keywords=prompt_response.keywords,
        image_url=image_url,
        artist_prompt=prompt_response.artist_prompt,
    )


async def _create_topic_p1(count: int = 1):
    tasks: list[Task[CombinedP1Response]] = []
    for _ in range(count):
        tasks.append(create_task(_create_question_p1()))

    return await gather(*tasks)


async def _update_topic_p1(
    id: str, status: bool, responses: list[CombinedP1Response] | BaseException | None
):
    try:
        task, topic_id = id.split(":")
        if task != "topic_1":
            return

        async def _update_inner(update_session: AsyncSession):
            topic = await _get_topic(topic_id, update_session)
            if not status or responses is None or isinstance(responses, BaseException):
                if isinstance(responses, ModelFailure):
                    topic.status = Status.service_failed
                else:
                    topic.status = Status.failed

            else:
                question_set: list[Question] = []
                for response in responses:
                    image_id = uuid4().__str__()
                    image_ext, image_data = cast(
                        tuple[str, str],
                        re.findall(BASE64_IMAGE_REGEX, response.image_url)[0],
                    )

                    filename = f"{image_id}.{image_ext}"
                    async with open(f"data/image/{filename}", "wb") as file:
                        await file.write(base64.b64decode(image_data))

                    question = Question(
                        topic_id=topic.id,
                        artist_prompt=response.artist_prompt,
                        keywords=response.keywords,
                        file=filename,
                    )
                    question_set.append(question)

                topic.status = Status.done
                update_session.add_all(question_set)

            update_session.add(topic)
            await update_session.commit()

        await create_session_and_run(_update_inner)

    except Exception:
        print(format_exc())


async def _update_topic_p2_3(
    id: str, status: bool, response: P2Response | P3Response | BaseException | None
):
    try:
        task, topic_id = id.split(":")
        if task != "topic_2_3":
            return

        async def _update_inner(update_session: AsyncSession):
            topic = await _get_topic(topic_id, update_session)
            question: Optional[Question] = None

            if not status or response is None or isinstance(response, BaseException):
                if isinstance(response, ModelFailure):
                    topic.status = Status.service_failed
                else:
                    topic.status = Status.failed

            else:
                question_str: str
                if isinstance(response, P2Response):
                    content = response.test_content
                    question_str = ""
                    if content.header:
                        question_str = (
                            f"**From:** {content.header.from_}\n"
                            + f"**To:** {content.header.to}\n"
                            + f"**Subject:** {content.header.subject}\n"
                            + f"**Sent:** {content.header.sent}\n"
                            + "\n"
                        )
                    question_str = (
                        question_str
                        + f"{content.body}\n"
                        + "\n"
                        + f"**Direction:** {content.direction}"
                    )
                elif isinstance(response, P3Response):
                    content = response.test_content
                    question_str = (
                        "**Directions:** Read the question below. "
                        + "You will have 30 minutes to plan, write, and revise your essay. "
                        + "Typically, an effective essay will contain a minimum of 300 words.\n"
                        + "\n"
                        + f"{content.context_statement}\n"
                        + f"{content.question_prompt}"
                    )

                topic.status = Status.done
                topic.summary = response.information
                question = Question(
                    topic_id=topic_id,
                    question=question_str,
                )

            update_session.add(topic)
            if question:
                update_session.add(question)
            await update_session.commit()

        await create_session_and_run(_update_inner)

    except Exception:
        print(format_exc())


async def create_topic(
    part: Literal["1", "2", "3"],
    p1_count: int = 5,
    _session: Optional[AsyncSession] = None,
):
    async def _inner(session: AsyncSession):
        topic: Topic

        if part == "1":
            id = uuid4().__str__()
            topic = Topic(
                id=id,
                status=Status.pending,
                part=TopicPart.I,
            )
            add_task(
                _create_topic_p1(count=p1_count),
                f"topic_1:{id}",
                callback=_update_topic_p1,
                event_loop=get_event_loop(),
            )

        elif part == "2" or part == "3":
            id = uuid4().__str__()
            topic = Topic(
                id=id,
                status=Status.pending,
                part=TopicPart.II if part == "2" else TopicPart.III,
            )
            add_task(
                cast(
                    Coroutine[Any, Any, P2Response | P3Response | None],
                    generate_topic(part=part),
                ),
                f"topic_2_3:{id}",
                callback=_update_topic_p2_3,
                event_loop=get_event_loop(),
            )
        session.add(topic)
        await session.commit()

        saved_topic = await _get_topic(topic.id, session)
        return format_topic(saved_topic)

    return await create_session_and_run(_inner, _session)


async def _insert_topic(
    part: Literal["2", "3"], question_str: str, _session: Optional[AsyncSession] = None
):
    async def _inner(session: AsyncSession):
        topic_id = uuid4().__str__()
        topic = Topic(
            id=topic_id,
            part=TopicPart.II if part == "2" else TopicPart.III,
            status=Status.done,
        )
        question = Question(topic_id=topic_id, question=question_str)
        session.add_all([topic, question])
        await session.commit()
        return await _get_topic(topic_id, session)

    return await create_session_and_run(_inner, _session)


async def insert_topic(
    part: Literal["2", "3"], question_str: str, _session: Optional[AsyncSession] = None
):
    return format_topic(await _insert_topic(part, question_str, _session))


async def delete_topic(id: str, _session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        topic = await _get_topic(id)
        await session.delete(topic)
        await session.commit()

    return await create_session_and_run(_inner, _session)


"""
SUBMISSION
"""


async def get_submissions(_session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        statement = select(Submission).order_by(desc(Submission.created_at))
        submissions = list((await session.execute(statement)).scalars().all())
        return [format_submission(submission) for submission in submissions]

    return await create_session_and_run(_inner, _session)


async def _get_submission(id: str, _session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        statement = (
            select(Submission)
            .where(Submission.id == id)
            .order_by(desc(Submission.created_at))
        )
        submission = (await session.execute(statement)).scalar()
        if not submission:
            raise SubmissionNotFound(id)
        return submission

    return await create_session_and_run(_inner, _session)


async def get_submission(id: str, _session: Optional[AsyncSession] = None):
    submission = await _get_submission(id, _session)
    return format_submission(submission)


async def get_submissions_of_topic(
    topic_id: str, _session: Optional[AsyncSession] = None
):
    topic = await get_topic(topic_id, _session)
    submissions = topic.submissions
    submissions.sort(key=lambda x: x.created_at)
    return submissions


class P1SubmitBody(BaseModel):
    file: str
    submission: str


async def p1_submit(
    topic_id: str,
    submissions: list[P1SubmitBody],
    _session: Optional[AsyncSession] = None,
):
    async def _inner(session: AsyncSession):
        topic = await _get_topic(topic_id, session)
        if topic.part != TopicPart.I:
            raise ValueError("wrong function")

        submission_id = uuid4().__str__()
        submission = Submission(id=submission_id, topic_id=topic_id)
        answers: list[Answer] = []
        for submission_ in submissions:
            question_statement = select(Question).where(Question.file == submission_.file)
            question = (await session.execute(question_statement)).scalar()
            if question is None or question.file is None:
                raise ValueError("question not found")
            question_submission = Answer(
                submission_id=submission_id,
                question_id=question.id,
                content=submission_.submission,
            )
            answers.append(question_submission)

        session.add_all([submission, *answers])
        await session.commit()

        new_submission = await _get_submission(submission.id)
        return format_submission(new_submission)

    return await create_session_and_run(_inner, _session)


async def p23_submit(
    topic_id: str,
    submitted_text: str,
    _session: Optional[AsyncSession] = None,
):
    async def _inner(session: AsyncSession):
        topic = await get_topic(topic_id, _session)

        if topic.part not in [TopicPart.II, TopicPart.III]:
            raise ValueError("wrong function")

        submission_id = uuid4().__str__()
        submission = Submission(id=submission_id, topic_id=topic.id)
        answer = Answer(
            submission_id=submission_id,
            question_id=cast(list[Question], topic.questions)[0].id,
            content=submitted_text,
        )
        session.add_all([submission, answer])
        await session.commit()

        new_submission = await _get_submission(submission.id)
        return format_submission(new_submission)

    return await create_session_and_run(_inner, _session)


# async def update_submission(
#     id: str, submitted_text: str, _session: Optional[AsyncSession] = None
# ):
#     async def _inner(session: AsyncSession):
#         submission = await _get_submission(id, session)
#         submission.submission = submitted_text
#         session.add(submission)
#         await session.commit()
#         return format_submission(submission)

#     return await create_session_and_run(_inner)


async def delete_submission(id: str, _session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        submission = await _get_submission(id)
        await session.delete(submission)
        await session.commit()

    return await create_session_and_run(_inner, _session)


"""
REVIEW
"""


async def get_reviews(_session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        statement = select(Review).order_by(desc(Review.created_at))
        reviews = list((await session.execute(statement)).scalars().all())
        return [format_review(review) for review in reviews]

    return await create_session_and_run(_inner, _session)


async def _get_review(id: str, _session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        statement = (
            select(Review).where(Review.id == id).order_by(desc(Review.created_at))
        )
        review = (await session.execute(statement)).scalar()
        if not review:
            raise ReviewNotFound(id)
        return review

    return await create_session_and_run(_inner, _session)


async def get_review(id: str, _session: Optional[AsyncSession] = None):
    review = await _get_review(id, _session)
    return format_review(review)


async def get_reviews_of_topic(topic_id: str, _session: Optional[AsyncSession] = None):
    topic = await get_topic(topic_id, _session)
    return topic.reviews


async def get_review_of_submission(
    submission_id: str, _session: Optional[AsyncSession] = None
):
    submission = await _get_submission(submission_id, _session)
    if submission.review:
        review = submission.review
        return format_review(review)
    return None


async def _inject_review(id: str, coro: Awaitable[T]) -> tuple[str, T]:
    return (id, await coro)


async def _review_p1(submission_id: str):
    async def _inner(session: AsyncSession):
        submission = await _get_submission(submission_id, session)
        tasks: list[Task[tuple[str, P1ReviewResponse]]] = []

        for answer in submission.answers:
            question = await _get_question(answer.question_id)
            if not question.file or not question.artist_prompt or not question.keywords:
                raise ValueError("missing p1 property")
            tasks.append(
                create_task(
                    coro=_inject_review(
                        answer.id,
                        cast(
                            Awaitable[P1ReviewResponse],
                            ai_review_p1(
                                file_path=f"data/image/{question.file}",
                                artist_prompt=question.artist_prompt,
                                keywords=question.keywords,
                                submission=answer.content,
                            ),
                        ),
                    )
                )
            )

        raw_responses = await gather(*tasks, return_exceptions=True)
        responses = []
        for response in raw_responses:
            if isinstance(response, tuple):
                responses.append(response)
            else:
                print("".join(format_exception(response)))
        overall = cast(
            ReviewResponse,
            await summary_review_p1([response[1] for response in responses]),
        )

        return (responses, overall)

    return await create_session_and_run(_inner)


async def _update_review_p1(
    id: str,
    status: bool,
    response: tuple[list[tuple[str, P1ReviewResponse]], ReviewResponse]
    | BaseException
    | None,
):
    try:
        task, review_id = id.split(":")
        if task != "review_p1":
            return

        async def _update_inner(update_session: AsyncSession):
            review = await _get_review(review_id, update_session)
            overall_review = None
            answer_reviews: list[AnswerReview] = []

            if not status or response is None or isinstance(response, BaseException):
                if isinstance(response, ModelFailure):
                    review.status = Status.service_failed
                else:
                    review.status = Status.failed

            else:
                review.status = Status.done

                review_responses, response_overall = response
                for answer_id, review_response in review_responses:
                    answer_reviews.append(
                        AnswerReview(
                            review_id=review.id,
                            answer_id=answer_id,
                            overall_score=review_response.overall_score,
                            feedback=review_response.feedback,
                            detail_score=review_response.detail_score,
                            annotations=review_response.annotations,
                        )
                    )
                overall_review = OverallReview(
                    review_id=review.id,
                    score_range=response_overall.score_range,
                    level_achieved=response_overall.level_achieved,
                    overall_feedback=response_overall.overall_feedback,
                    summary_feedback=response_overall.summary_feedback,
                    detail_score=response_overall.detail_score,
                    annotations=response_overall.annotations,
                    improvement_suggestions=response_overall.improvement_suggestions,
                )

            update_session.add(review)
            if answer_reviews.__len__():
                update_session.add_all(answer_reviews)
            if overall_review:
                update_session.add(overall_review)
            await update_session.commit()

        await create_session_and_run(_update_inner)
    except Exception:
        print(format_exc())


async def _update_review_p2_3(
    id: str, status: bool, response: ReviewResponse | BaseException | None
):
    try:
        task, review_id = id.split(":")
        if task != "review_p2_3":
            return

        async def _update_inner(update_session: AsyncSession):
            review = await _get_review(review_id, update_session)
            overall_review = None

            if not status or response is None or isinstance(response, BaseException):
                if isinstance(response, ModelFailure):
                    review.status = Status.service_failed
                else:
                    review.status = Status.failed

            else:
                review.status = Status.done
                overall_review = OverallReview(
                    review_id=review.id,
                    score_range=response.score_range,
                    level_achieved=response.level_achieved,
                    overall_feedback=response.overall_feedback,
                    summary_feedback=response.summary_feedback,
                    detail_score=response.detail_score,
                    annotations=response.annotations,
                    improvement_suggestions=response.improvement_suggestions,
                )

            update_session.add(review)
            if overall_review:
                update_session.add(overall_review)
            await update_session.commit()

        await create_session_and_run(_update_inner)
    except Exception:
        print(format_exc())


async def review(submission_id: str, _session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        submission = await _get_submission(submission_id, session)
        topic = submission.topic
        if not topic:
            raise TopicNotFound()

        id = uuid4().__str__()
        review_obj = Review(
            id=id,
            topic_id=topic.id,
            submission_id=submission_id,
            status=Status.pending,
        )

        if topic.part == TopicPart.I:
            add_task(
                _review_p1(submission_id),
                f"review_p1:{id}",
                callback=_update_review_p1,
                event_loop=get_event_loop(),
            )
        elif topic.part in [TopicPart.II, TopicPart.III]:
            answer = submission.answers[0].content
            add_task(
                ai_review_p2_3(
                    part=topic.part.value,
                    topic=cast(str, topic.questions[0].question),
                    submission=answer,
                ),
                f"review_p2_3:{id}",
                callback=_update_review_p2_3,
                event_loop=get_event_loop(),
            )

        session.add(review_obj)
        await session.commit()
        return (review_obj, id)

    return await create_session_and_run(_inner, _session)


async def delete_review(id: str, _session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        statement = delete(Review).where(col(Review.id) == id)
        await session.execute(statement)
        await session.commit()

    return await create_session_and_run(_inner, _session)


"""
STATICS
"""


async def get_sessions(_session: Optional[AsyncSession] = None):
    async def _inner(session: AsyncSession):
        statements = select(Session)

        return list((await session.execute(statements)).scalars().all())

    return await create_session_and_run(_inner, _session)


async def add_session(
    start: datetime, end: datetime, _session: Optional[AsyncSession] = None
):
    async def _inner(session: AsyncSession):
        _session = Session(started_at=start, ended_at=end)
        session.add(_session)
        await session.commit()
        return _session

    return await create_session_and_run(_inner, _session)


async def statistics():
    async def _inner(session: AsyncSession):
        topics = await get_topics()
        reviews = filter(lambda x: x.overall is not None, await get_reviews(session))

        mid_points: list[float] = []
        for review in reviews:
            score_range = cast(OverallReview, review.overall).score_range
            mid_points.append((score_range[0] + score_range[1]) / 2)

        average_score = sum(mid_points) / len(mid_points) if len(mid_points) else 0

        sessions = await get_sessions(session)
        total_time = sum(
            [(session.started_at - session.ended_at).microseconds for session in sessions]
        )

        submissions = await get_submissions(session)

        return Statistics(
            total_submission=submissions.__len__(),
            total_topic=topics.__len__(),
            average_score=average_score,
            total_time=total_time,
        )

    return await create_session_and_run(_inner)
