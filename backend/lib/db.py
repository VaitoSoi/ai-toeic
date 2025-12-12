from asyncio import get_event_loop
from datetime import datetime
from enum import Enum
from traceback import format_exc
from typing import Awaitable, Callable, Literal, Optional, TypeVar, cast
from uuid import uuid4

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
    Field,
    Relationship,
    SQLModel,
    desc,
    select,
)

from .ai import (
    Annotation,
    DetailScore,
    ReviewResponse,
    SummaryResponse,
    generate_topic,
    review as ai_review,
    summary,
)
from .env import DB_URL
from .exception import ReviewNotFound, SubmissionNotFound, TopicNotFound
from .task import add_task
from .util import PydanticJSON, PydanticListJSON


class TopicType(Enum):
    writing = "writing"


class TopicPart(Enum):
    II = "2"
    III = "3"


class Topic(SQLModel, table=True):
    __tablename__ = "topic"  # type: ignore

    id: str = Field(primary_key=True, default_factory=lambda: uuid4().__str__())

    type: TopicType = Field(default=TopicType.writing)
    part: TopicPart
    question: str
    summary: Optional[SummaryResponse] = Field(
        default=None, sa_type=PydanticJSON(SummaryResponse)
    )

    submissions: list["Submission"] = Relationship(back_populates="topic")
    reviews: list["Review"] = Relationship(back_populates="topic")

    created_at: datetime = Field(default_factory=lambda: datetime.now())


class SlicedTopic(BaseModel):
    id: str

    type: TopicType
    part: TopicPart
    question: str
    summary: Optional[SummaryResponse]

    submissions: list["BaseSubmission"] = PydanticField(default=[])
    reviews: list["SlicedReview"] = PydanticField(default=[])

    created_at: datetime


class BaseSubmission(SQLModel, table=False):
    id: str
    topic_id: str
    submission: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class Submission(BaseSubmission, table=True):
    __tablename__ = "submission"  # type: ignore
    id: str = Field(primary_key=True, default_factory=lambda: uuid4().__str__())

    topic_id: str = Field(foreign_key="topic.id", ondelete="CASCADE")
    topic: Topic = Relationship(back_populates="submissions")

    review: Optional["Review"] = Relationship(back_populates="submission")


class SlicedSubmission(BaseModel):
    id: str
    topic_id: str
    submission: str
    review: Optional["SlicedReview"] = PydanticField(default=None)
    created_at: datetime


class ReviewStatus(Enum):
    reviewing = "reviewing"
    failed = "failed"
    done = "done"


class Review(SQLModel, table=True):
    __tablename__ = "review"  # type: ignore

    id: str = Field(primary_key=True, default_factory=lambda: uuid4().__str__())

    topic_id: str = Field(foreign_key="topic.id", ondelete="CASCADE")
    topic: Topic = Relationship(back_populates="reviews")

    submission_id: str = Field(foreign_key="submission.id", ondelete="CASCADE")
    submission: Submission = Relationship(back_populates="review")

    status: ReviewStatus

    score_range: Optional[tuple[int, int]] = Field(default=None, sa_column=Column(JSON))
    level_achieved: Optional[int] = Field(default=None)
    overall_feedback: Optional[str] = Field(default=None)
    summary_feedback: Optional[str] = Field(default=None)
    detail_score: Optional[DetailScore] = Field(
        default=None, sa_type=PydanticJSON(DetailScore)
    )
    annotations: Optional[list[Annotation]] = Field(
        default=None, sa_type=PydanticListJSON(Annotation)
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now())


class SlicedReview(BaseModel):
    id: str

    topic_id: str
    submission_id: str

    status: ReviewStatus

    score_range: Optional[tuple[int, int]] = PydanticField(default=None)
    level_achieved: Optional[int] = PydanticField(default=None)
    overall_feedback: Optional[str] = PydanticField(default=None)
    summary_feedback: Optional[str] = PydanticField(default=None)
    detail_score: Optional[DetailScore] = PydanticField(default=None)
    annotations: Optional[list[Annotation]] = PydanticField(default=None)

    created_at: datetime


class Session(SQLModel, table=True):
    __tablename__ = "session"  # type: ignore

    id: str = Field(primary_key=True, default_factory=lambda: uuid4().__str__())

    started_at: datetime
    ended_at: datetime

    created_at: datetime = Field(default_factory=lambda: datetime.now())


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
TOPIC
"""


async def get_topics(_session: AsyncSession | None = None):
    async def _inner(session: AsyncSession):
        statement = (
            select(Topic)
            .order_by(desc(Topic.created_at))
            .options(
                selectinload(Topic.submissions),  # type: ignore
                selectinload(Topic.reviews),  # type: ignore
            )
        )
        topics = list((await session.execute(statement)).scalars().all())
        return [
            SlicedTopic(
                id=topic.id,
                type=topic.type,
                part=topic.part,
                question=topic.question,
                summary=topic.summary,
                submissions=[
                    BaseSubmission(**sub.model_dump()) for sub in topic.submissions
                ],
                reviews=[
                    SlicedReview(**review.model_dump()) for review in topic.reviews
                ],
                created_at=topic.created_at,
            )
            for topic in topics
        ]

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
            )
        )
        topic = (await session.execute(statement)).scalar()
        if not topic:
            raise TopicNotFound(id)

        return topic

    return await create_session_and_run(_inner, _session)


async def get_topic(id: str, _session: AsyncSession | None = None):
    topic = await _get_topic(id, _session)
    return SlicedTopic(
        id=topic.id,
        type=topic.type,
        part=topic.part,
        question=topic.question,
        summary=topic.summary,
        submissions=[BaseSubmission(**sub.model_dump()) for sub in topic.submissions],
        reviews=[SlicedReview(**review.model_dump()) for review in topic.reviews],
        created_at=topic.created_at,
    )


async def create_topic(
    part: Literal["2"] | Literal["3"], _session: AsyncSession | None = None
):
    question = await generate_topic(part)

    async def _inner(session: AsyncSession):
        topic = Topic(
            part=TopicPart.II if part == "2" else TopicPart.III,
            question=question,
            summary=await summary(question),
        )
        session.add(topic)
        await session.commit()
        return SlicedTopic(
            id=topic.id,
            type=topic.type,
            part=topic.part,
            question=topic.question,
            summary=topic.summary,
            submissions=[],
            reviews=[],
            created_at=topic.created_at,
        )

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
        return [
            SlicedSubmission(
                id=submission.id,
                topic_id=submission.topic_id,
                submission=submission.submission,
                review=SlicedReview(**submission.review.model_dump())
                if submission.review
                else None,
                created_at=submission.created_at,
            )
            for submission in submissions
        ]

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
    return SlicedSubmission(
        id=submission.id,
        topic_id=submission.topic_id,
        submission=submission.submission,
        review=SlicedReview(**submission.review.model_dump())
        if submission.review
        else None,
        created_at=submission.created_at,
    )


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
        return SlicedSubmission(
            id=submission.id,
            topic_id=submission.topic_id,
            submission=submission.submission,
            review=None,
            created_at=submission.created_at,
        )

    return await create_session_and_run(_inner, _session)


async def update_submission(
    id: str, submitted_text: str, _session: AsyncSession | None = None
):
    async def _inner(session: AsyncSession):
        submission = await _get_submission(id, session)
        submission.submission = submitted_text
        session.add(submission)
        await session.commit()
        return SlicedSubmission(
            id=submission.id,
            topic_id=submission.topic_id,
            submission=submission.submission,
            review=SlicedReview(**submission.review.model_dump())
            if submission.review
            else None,
            created_at=submission.created_at,
        )

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
        return [
            SlicedReview(
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
                created_at=review.created_at,
            )
            for review in reviews
        ]

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
        created_at=review.created_at,
    )


async def get_reviews_of_topic(topic_id: str, _session: AsyncSession | None = None):
    topic = await get_topic(topic_id, _session)
    return topic.reviews


async def get_review_of_submission(
    submission_id: str, _session: AsyncSession | None = None
):
    submission = await _get_submission(submission_id, _session)
    if submission.review:
        review = submission.review
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
            created_at=review.created_at,
        )
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
                        review.status = ReviewStatus.failed
                    else:
                        review.status = ReviewStatus.done
                        review.score_range = response.score_range
                        review.level_achieved = response.level_achieved
                        review.overall_feedback = response.overall_feedback
                        review.summary_feedback = response.summary_feedback
                        review.detail_score = response.detail_score
                        review.annotations = response.annotations
                    update_session.add(review)
                    await update_session.commit()

                await create_session_and_run(_update_inner)
            except Exception:
                print(format_exc())

        id = uuid4().__str__()
        add_task(
            ai_review(
                part=topic.part.value,
                topic=topic.question,
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
            status=ReviewStatus.reviewing,
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
        reviews = filter(
            lambda x: x.score_range is not None, await get_reviews(session)
        )

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
            [
                (session.started_at - session.ended_at).microseconds
                for session in sessions
            ]
        )

        submissions = await get_submissions(session)

        return Statistics(
            total_submission=submissions.__len__(),
            average_score=average_score,
            improvement_rate=improvement_rate,
            total_time=total_time,
        )

    return await create_session_and_run(_inner)
