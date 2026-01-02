import base64
import re
from asyncio import Task, create_task, gather, get_event_loop
from datetime import datetime
from enum import Enum as PyEnum
from traceback import format_exc
from typing import Any, Awaitable, Callable, Coroutine, Literal, Optional, TypeVar, cast
from uuid import uuid4

from aiofiles import open
from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import selectinload
from sqlmodel import (
    JSON,
    Column,
    Enum as SQLEnum,
    Field as SQLField,
    Relationship,
    SQLModel,
    desc,
    select,
)

from .ai import (
    Annotation,
    DetailScore,
    P1Response,
    P2Response,
    P3Response,
    ReviewResponse,
    Summary,
    generate_image,
    generate_topic,
    review as ai_review,
)
from .env import DB_URL
from .exception import ReviewNotFound, SubmissionNotFound, TopicNotFound
from .task import add_task
from .util import PydanticJSON, PydanticListJSON


class Status(PyEnum):
    pending = "pending"
    failed = "failed"
    done = "done"


class TopicType(PyEnum):
    writing = "writing"


class TopicPart(PyEnum):
    I = "1"  # noqa: E741
    II = "2"
    III = "3"


class Topic(SQLModel, table=True):
    __tablename__ = "topic"  # pyright: ignore[reportAssignmentType]

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    status: Status = SQLField(sa_column=Column(SQLEnum(Status)))

    type: TopicType = SQLField(
        default=TopicType.writing, sa_column=Column(SQLEnum(TopicType))
    )
    part: TopicPart = SQLField(sa_column=Column(SQLEnum(TopicPart)))

    question: Optional[str] = SQLField(default=None)  # Part 2 & 3
    question_set: Optional[list["TopicQuestion"]] = Relationship(
        back_populates="topic"
    )  # Part 1

    summary: Optional[Summary] = SQLField(default=None, sa_type=PydanticJSON(Summary))

    submissions: list["Submission"] = Relationship(back_populates="topic")
    reviews: list["Review"] = Relationship(back_populates="topic")

    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class TopicQuestion(SQLModel, table=True):
    __tablename__ = "topic_question"  # pyright: ignore[reportAssignmentType]

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    topic_id: str = SQLField(foreign_key="topic.id")
    topic: Topic = Relationship(back_populates="question_set")

    artist_prompt: str
    file: str
    keywords: tuple[str, str] = SQLField(sa_column=Column(JSON))

    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class SlicedTopic(BaseModel):
    id: str

    status: Status

    type: TopicType
    part: TopicPart

    question: Optional[str]
    question_set: Optional[list["SlicedTopicQuestion"]]

    submissions: list["SlicedSubmission"] = PydanticField(default=[])
    reviews: list["SlicedReview"] = PydanticField(default=[])

    summary: Optional[Summary]

    created_at: datetime


class SlicedTopicQuestion(BaseModel):
    id: str
    topic_id: str
    artist_prompt: str
    file: str
    keywords: tuple[str, str]
    created_at: datetime


class Submission(SQLModel, table=True):
    __tablename__ = "submission"  # type: ignore
    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())
    topic_id: str
    submission: str

    topic_id: str = SQLField(foreign_key="topic.id", ondelete="CASCADE")
    topic: Topic = Relationship(back_populates="submissions")

    review: Optional["Review"] = Relationship(back_populates="submission")
    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class SlicedSubmission(BaseModel):
    id: str
    topic_id: str
    submission: str
    review: Optional["SlicedReview"] = PydanticField(default=None)
    created_at: datetime


class Review(SQLModel, table=True):
    __tablename__ = "review"  # type: ignore

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    topic_id: str = SQLField(foreign_key="topic.id", ondelete="CASCADE")
    topic: Topic = Relationship(back_populates="reviews")

    submission_id: str = SQLField(foreign_key="submission.id", ondelete="CASCADE")
    submission: Submission = Relationship(back_populates="review")

    status: Status

    score_range: Optional[tuple[int, int]] = SQLField(
        default=None, sa_column=Column(JSON)
    )
    level_achieved: Optional[int] = SQLField(default=None)
    overall_feedback: Optional[str] = SQLField(default=None)
    summary_feedback: Optional[str] = SQLField(default=None)
    detail_score: Optional[DetailScore] = SQLField(
        default=None, sa_type=PydanticJSON(DetailScore)
    )
    annotations: Optional[list[Annotation]] = SQLField(
        default=None, sa_type=PydanticListJSON(Annotation)
    )
    improvement_suggestions: Optional[list[str]] = SQLField(
        default=None, sa_column=Column(JSON)
    )

    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class SlicedReview(BaseModel):
    id: str

    topic_id: str
    submission_id: str

    status: Status

    score_range: Optional[tuple[int, int]] = PydanticField(default=None)
    level_achieved: Optional[int] = PydanticField(default=None)
    overall_feedback: Optional[str] = PydanticField(default=None)
    summary_feedback: Optional[str] = PydanticField(default=None)
    detail_score: Optional[DetailScore] = PydanticField(default=None)
    annotations: Optional[list[Annotation]] = PydanticField(default=None)
    improvement_suggestions: Optional[list[str]] = PydanticField(default=None)

    created_at: datetime


class Session(SQLModel, table=True):
    __tablename__ = "session"  # type: ignore

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    started_at: datetime
    ended_at: datetime

    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class Statistics(BaseModel):
    total_submission: int
    average_score: float
    improvement_rate: float
    total_time: int


engine = create_async_engine(DB_URL)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


T = TypeVar("T")


async def create_session_and_run(
    func: Callable[[AsyncSession], Awaitable[T]],
    _session: AsyncSession | None = None,
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
        status=topic.status,
        type=topic.type,
        part=topic.part,
        summary=topic.summary,
        question=topic.question,
        question_set=[format_topic_question(question) for question in topic.question_set]
        if topic.question_set
        else None,
        submissions=[format_submission(sub) for sub in topic.submissions],
        reviews=[format_review(review) for review in topic.reviews],
        created_at=topic.created_at,
    )


def format_topic_question(question: TopicQuestion):
    return SlicedTopicQuestion(
        id=question.id,
        topic_id=question.topic_id,
        artist_prompt=question.artist_prompt,
        file=question.file,
        keywords=question.keywords,
        created_at=question.created_at,
    )


def format_submission(submission: Submission):
    return SlicedSubmission(
        id=submission.id,
        topic_id=submission.topic_id,
        submission=submission.submission,
        review=format_review(submission.review) if submission.review else None,
        created_at=submission.created_at,
    )


def format_review(review: Review):
    return SlicedReview(
        id=review.id,
        topic_id=review.topic_id,
        submission_id=review.submission_id,
        status=review.status,
        score_range=review.score_range,
        level_achieved=review.level_achieved,
        overall_feedback=review.overall_feedback,
        summary_feedback=review.summary_feedback,
        detail_score=review.detail_score,
        annotations=review.annotations,
        improvement_suggestions=review.improvement_suggestions,
        created_at=review.created_at,
    )


"""
TOPIC
"""


async def get_topics(all: bool = False, _session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        statement = (
            select(Topic)
            .order_by(desc(Topic.created_at))
            .options(
                selectinload(Topic.submissions),  # type: ignore
                selectinload(Topic.reviews),  # type: ignore
                selectinload(Topic.question_set),  # type: ignore
            )
        )
        if not all:
            statement = statement.where(Topic.status == Status.done)
        topics = list((await session.execute(statement)).scalars().all())
        return [format_topic(topic) for topic in topics]

    return await create_session_and_run(_inner, _session)


async def _get_topic(id: str, _session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        statement = (
            select(Topic)
            .where(Topic.id == id)
            .order_by(desc(Topic.created_at))
            .options(
                selectinload(Topic.submissions),  # type: ignore
                selectinload(Topic.reviews),  # type: ignore
                selectinload(Topic.question_set),  # type: ignore
            )
        )
        topic = (await session.execute(statement)).scalar()
        if not topic:
            raise TopicNotFound(id)

        return topic

    return await create_session_and_run(_inner, _session)


async def get_topic(id: str, _session: AsyncSession | None = None):
    topic = await _get_topic(id, _session)
    return format_topic(topic)


class CombinedP1Response(BaseModel):
    prompt: str
    keywords: tuple[str, str]
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
        prompt=prompt_response.artist_prompt,
        keywords=prompt_response.keywords,
        image_url=image_url,
    )


async def _create_topic_p1(count: int = 1):
    tasks: list[Task[CombinedP1Response]] = []
    for _ in range(count):
        tasks.append(create_task(_create_question_p1()))

    return await gather(*tasks)


async def _update_topic_p1(
    id: str, status: bool, responses: list[CombinedP1Response] | None
):
    try:
        task, topic_id = id.split(":")
        if task != "topic_1":
            return

        async def _update_inner(update_session: AsyncSession):
            topic = await _get_topic(topic_id, update_session)
            if not status or responses is None:
                topic.status = Status.failed

            else:
                question_set: list[TopicQuestion] = []
                for response in responses:
                    image_id = uuid4().__str__()
                    image_ext, image_data = cast(
                        tuple[str, str],
                        re.findall(BASE64_IMAGE_REGEX, response.image_url)[0],
                    )

                    filename = f"{image_id}.{image_ext}"
                    async with open(f"data/image/{filename}", "wb") as file:
                        await file.write(base64.b64decode(image_data))

                    question = TopicQuestion(
                        topic_id=topic.id,
                        artist_prompt=response.prompt,
                        keywords=response.keywords,
                        file=filename,
                    )
                    question_set.append(question)

                topic.status = Status.done

                update_session.add_all([topic, *question_set])
                await update_session.commit()

        await create_session_and_run(_update_inner)

    except Exception:
        print(format_exc())


async def _update_topic_p2_3(
    id: str, status: bool, response: P2Response | P3Response | None
):
    try:
        task, topic_id = id.split(":")
        if task != "topic_2_3":
            return

        async def _update_inner(update_session: AsyncSession):
            topic = await _get_topic(topic_id, update_session)
            if not status or response is None:
                topic.status = Status.failed
            else:
                question: str
                if isinstance(response, P2Response):
                    content = response.test_content
                    question = (
                        f"**From:** {content.email_header.from_}\n"
                        + f"**To:** {content.email_header.to}\n"
                        + f"**Subject:** {content.email_header.subject}\n"
                        + f"**Sent:** {content.email_header.sent}\n"
                        + "\n"
                        + f"{content.email_body}\n"
                        + "\n"
                        + f"**Direction:** {content.direction}"
                    )
                elif isinstance(response, P3Response):
                    content = response.test_content
                    question = (
                        "**Directions:** Read the question below. "
                        + "You will have 30 minutes to plan, write, and revise your essay. "
                        + "Typically, an effective essay will contain a minimum of 300 words.\n"
                        + "\n"
                        + f"{content.context_statement}\n"
                        + f"{content.question_prompt}"
                    )

                print(question)

                topic.status = Status.done
                topic.summary = response.information
                topic.question = question

            update_session.add(topic)
            await update_session.commit()

        await create_session_and_run(_update_inner)

    except Exception:
        print(format_exc())


async def create_topic(
    part: Literal["1", "2", "3"],
    p1_count: int = 5,
    _session: AsyncSession | None = None,
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


async def delete_topic(id: str, _session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        topic = await _get_topic(id)
        await session.delete(topic)
        await session.commit()

    return await create_session_and_run(_inner, _session)


"""
SUBMISSION
"""


async def get_submissions(_session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        statement = (
            select(Submission)
            .order_by(desc(Submission.created_at))
            .options(selectinload(Submission.topic), selectinload(Submission.review))  # type: ignore
        )
        submissions = list((await session.execute(statement)).scalars().all())
        return [format_submission(submission) for submission in submissions]

    return await create_session_and_run(_inner, _session)


async def _get_submission(id: str, _session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        statement = (
            select(Submission)
            .where(Submission.id == id)
            .order_by(desc(Submission.created_at))
            .options(selectinload(Submission.topic), selectinload(Submission.review))  # type: ignore
        )
        submission = (await session.execute(statement)).scalar()
        if not submission:
            raise SubmissionNotFound(id)
        return submission

    return await create_session_and_run(_inner, _session)


async def get_submission(id: str, _session: AsyncSession | None = None):
    submission = await _get_submission(id, _session)
    return format_submission(submission)


async def get_submissions_of_topic(topic_id: str, _session: AsyncSession | None = None):
    topic = await get_topic(topic_id, _session)
    return topic.submissions


async def submit(
    topic_id: str, submitted_text: str, _session: AsyncSession | None = None
):
    async def _inner(session: AsyncSession):
        topic = await get_topic(topic_id, _session)
        submission = Submission(topic_id=topic.id, submission=submitted_text)
        session.add(submission)
        await session.commit()
        return format_submission(submission)

    return await create_session_and_run(_inner, _session)


async def update_submission(
    id: str, submitted_text: str, _session: AsyncSession | None = None
):
    async def _inner(session: AsyncSession):
        submission = await _get_submission(id, session)
        submission.submission = submitted_text
        session.add(submission)
        await session.commit()
        return format_submission(submission)

    return await create_session_and_run(_inner)


async def delete_submission(id: str, _session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        submission = await _get_submission(id)
        await session.delete(submission)
        await session.commit()

    return await create_session_and_run(_inner, _session)


"""
REVIEW
"""


async def get_reviews(_session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        statement = select(Review).order_by(desc(Review.created_at))
        reviews = list((await session.execute(statement)).scalars().all())
        return [format_review(review) for review in reviews]

    return await create_session_and_run(_inner, _session)


async def _get_review(id: str, _session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        statement = (
            select(Review)
            .where(Review.id == id)
            .order_by(desc(Review.created_at))
            .options(selectinload(Review.topic), selectinload(Review.submission))  # type: ignore
        )
        review = (await session.execute(statement)).scalar()
        if not review:
            raise ReviewNotFound(id)
        return review

    return await create_session_and_run(_inner, _session)


async def get_review(id: str, _session: AsyncSession | None = None):
    review = await _get_review(id, _session)
    return format_review(review)


async def get_reviews_of_topic(topic_id: str, _session: AsyncSession | None = None):
    topic = await get_topic(topic_id, _session)
    return topic.reviews


async def get_review_of_submission(
    submission_id: str, _session: AsyncSession | None = None
):
    submission = await _get_submission(submission_id, _session)
    if submission.review:
        review = submission.review
        return format_review(review)
    return None


async def review(submission_id: str, _session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        submission = await _get_submission(submission_id, session)
        topic = submission.topic
        if not topic:
            raise TopicNotFound()

        async def update_review(id: str, status: bool, response: ReviewResponse | None):
            try:
                task, review_id = id.split(":")
                if task != "review":
                    return

                async def _update_inner(update_session: AsyncSession):
                    review = await _get_review(review_id, update_session)
                    if not status or response is None:
                        review.status = Status.failed
                    else:
                        review.status = Status.done
                        review.score_range = response.score_range
                        review.level_achieved = response.level_achieved
                        review.overall_feedback = response.overall_feedback
                        review.summary_feedback = response.summary_feedback
                        review.detail_score = response.detail_score
                        review.annotations = response.annotations
                        review.improvement_suggestions = response.improvement_suggestions
                    update_session.add(review)
                    await update_session.commit()

                await create_session_and_run(_update_inner)
            except Exception:
                print(format_exc())

        id = uuid4().__str__()
        add_task(
            ai_review(
                part=topic.part.value,
                topic=cast(str, topic.question),
                submission=submission.submission,
            ),
            f"review:{id}",
            callback=update_review,
            event_loop=get_event_loop(),
        )
        review_obj = Review(
            id=id,
            submission_id=submission.id,
            topic_id=topic.id,
            status=Status.pending,
        )
        session.add(review_obj)
        await session.commit()
        return (review_obj, id)

    return await create_session_and_run(_inner, _session)


"""
STATICS
"""


async def get_sessions(_session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        statements = select(Session)

        return list((await session.execute(statements)).scalars().all())

    return await create_session_and_run(_inner, _session)


async def add_session(
    start: datetime, end: datetime, _session: AsyncSession | None = None
):
    async def _inner(session: AsyncSession):
        _session = Session(started_at=start, ended_at=end)
        session.add(_session)
        await session.commit()
        return _session

    return await create_session_and_run(_inner, _session)


async def statistics():
    async def _inner(session: AsyncSession):
        reviews = filter(lambda x: x.score_range is not None, await get_reviews(session))

        mid_points: list[float] = []
        for review in reviews:
            score_range = cast(tuple[int, int], review.score_range)
            mid_points.append((score_range[0] + score_range[1]) / 2)

        average_score = sum(mid_points) / len(mid_points) if len(mid_points) else 0
        improvement_rate = (
            (mid_points[0] + mid_points[-1]) / mid_points[0]
            if len(mid_points) and mid_points[0]
            else 0
        )

        sessions = await get_sessions(session)
        total_time = sum(
            [(session.started_at - session.ended_at).microseconds for session in sessions]
        )

        submissions = await get_submissions(session)

        return Statistics(
            total_submission=submissions.__len__(),
            average_score=average_score,
            improvement_rate=improvement_rate,
            total_time=total_time,
        )

    return await create_session_and_run(_inner)
