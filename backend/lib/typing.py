from datetime import datetime
from enum import Enum as PyEnum
from random import choice
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import (
    JSON,
    Column,
    Enum as SQLEnum,
    Field as SQLField,
    Relationship,
    SQLModel,
)

from .util import PydanticJSON, PydanticListJSON, colors

"""
AI API related models
"""

class Annotation(SQLModel):
    target_text: str
    context_before: str
    type: Literal["grammar", "vocabulary", "coherence", "mechanics", "suggestion"]
    replacement: str | None
    feedback: str


class DetailScore(SQLModel):
    grammar: int
    vocabulary: int
    organization: int
    task_fulfillment: int


class P1DetailScore(SQLModel):
    grammar: int
    visual_relevance: int


class Summary(SQLModel):
    summary: str
    description: str
    

"""
Database related models
"""

class Status(PyEnum):
    pending = "pending"
    failed = "failed"
    service_failed = "service_failed"
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
    color: str = SQLField(default_factory=lambda: choice(colors))

    status: Status = SQLField(sa_column=Column(SQLEnum(Status)))

    type: TopicType = SQLField(
        default=TopicType.writing, sa_column=Column(SQLEnum(TopicType))
    )
    part: TopicPart = SQLField(sa_column=Column(SQLEnum(TopicPart)))

    questions: list["Question"] = Relationship(
        back_populates="topic", sa_relationship_kwargs={"lazy": "selectin"}
    )  # Part 1
    summary: Optional[Summary] = SQLField(default=None, sa_type=PydanticJSON(Summary))

    submissions: list["Submission"] = Relationship(
        back_populates="topic", sa_relationship_kwargs={"lazy": "selectin"}
    )
    reviews: list["Review"] = Relationship(
        back_populates="topic", sa_relationship_kwargs={"lazy": "selectin"}
    )

    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class Question(SQLModel, table=True):
    __tablename__ = "question"  # type: ignore

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    topic_id: str = SQLField(foreign_key="topic.id", ondelete="CASCADE")
    topic: Topic = Relationship(
        back_populates="questions", sa_relationship_kwargs={"lazy": "selectin"}
    )

    question: Optional[str] = SQLField(default=None)

    artist_prompt: Optional[str] = SQLField(default=None)
    file: Optional[str] = SQLField(default=None, unique=True)
    keywords: Optional[tuple[str, str]] = SQLField(default=None, sa_column=Column(JSON))

    answers: list["Answer"] = Relationship(
        back_populates="question", sa_relationship_kwargs={"lazy": "selectin"}
    )

    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class SlicedTopic(BaseModel):
    id: str
    color: str

    status: Status

    type: TopicType
    part: TopicPart

    questions: Optional[list["SlicedTopicQuestion"]] = PydanticField(default=[])

    submissions: list["SlicedSubmission"] = PydanticField(default=[])
    reviews: list["SlicedReview"] = PydanticField(default=[])

    summary: Optional[Summary]

    created_at: datetime


class SlicedTopicQuestion(BaseModel):
    id: str
    topic_id: str
    question: Optional[str]
    artist_prompt: Optional[str]
    file: Optional[str]
    keywords: Optional[tuple[str, str]]
    created_at: datetime


class Submission(SQLModel, table=True):
    __tablename__ = "submission"  # type: ignore
    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    topic_id: str = SQLField(foreign_key="topic.id", ondelete="CASCADE")
    topic: Topic = Relationship(
        back_populates="submissions", sa_relationship_kwargs={"lazy": "selectin"}
    )

    answers: list["Answer"] = Relationship(
        back_populates="submission", sa_relationship_kwargs={"lazy": "selectin"}
    )

    review: Optional["Review"] = Relationship(
        back_populates="submission", sa_relationship_kwargs={"lazy": "selectin"}
    )
    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class Answer(SQLModel, table=True):
    __tablename__ = "answer"  # type: ignore

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    question_id: str = SQLField(foreign_key="question.id", ondelete="CASCADE")
    question: Question = Relationship(
        back_populates="answers", sa_relationship_kwargs={"lazy": "selectin"}
    )

    submission_id: str = SQLField(foreign_key="submission.id", ondelete="CASCADE")
    submission: Submission = Relationship(
        back_populates="answers", sa_relationship_kwargs={"lazy": "selectin"}
    )

    content: str

    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class SlicedSubmission(BaseModel):
    id: str
    topic_id: str
    answers: list["SlicedAnswer"] = PydanticField(default=[])
    review: Optional["SlicedReview"] = PydanticField(default=None)
    created_at: datetime


class SlicedAnswer(BaseModel):
    id: str
    question_id: str
    submission_id: str
    content: str
    created_at: datetime


class Review(SQLModel, table=True):
    __tablename__ = "review"  # type: ignore

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    topic_id: str = SQLField(foreign_key="topic.id", ondelete="CASCADE")
    topic: Topic = Relationship(
        back_populates="reviews", sa_relationship_kwargs={"lazy": "selectin"}
    )

    submission_id: str = SQLField(foreign_key="submission.id", ondelete="CASCADE")
    submission: Submission = Relationship(
        back_populates="review", sa_relationship_kwargs={"lazy": "selectin"}
    )

    status: Status

    overall: Optional["OverallReview"] = Relationship(
        back_populates="review", sa_relationship_kwargs={"lazy": "selectin"}
    )
    answers: Optional[list["AnswerReview"]] = Relationship(
        back_populates="review", sa_relationship_kwargs={"lazy": "selectin"}
    )

    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class OverallReview(SQLModel, table=True):
    __tablename__ = "overall_review"  # type: ignore

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    review_id: str = SQLField(foreign_key="review.id", ondelete="CASCADE")
    review: Review = Relationship(
        back_populates="overall", sa_relationship_kwargs={"lazy": "selectin"}
    )

    score_range: tuple[int, int] = SQLField(sa_column=Column(JSON))
    level_achieved: int
    overall_feedback: str
    summary_feedback: str
    detail_score: DetailScore = SQLField(sa_type=PydanticJSON(DetailScore))
    annotations: list[Annotation] = SQLField(sa_type=PydanticListJSON(Annotation))
    improvement_suggestions: list[str] = SQLField(sa_column=Column(JSON))


class AnswerReview(SQLModel, table=True):
    __tablename__ = "answer_review"  # type: ignore

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    review_id: str = SQLField(foreign_key="review.id", ondelete="CASCADE")
    review: Review = Relationship(
        back_populates="answers", sa_relationship_kwargs={"lazy": "selectin"}
    )

    answer_id: str = SQLField(foreign_key="answer.id", ondelete="CASCADE")
    answer: Answer = Relationship(sa_relationship_kwargs={"lazy": "selectin"})

    overall_score: int
    feedback: str
    detail_score: P1DetailScore = SQLField(sa_type=PydanticJSON(P1DetailScore))
    annotations: list[Annotation] = SQLField(sa_type=PydanticListJSON(Annotation))


class SlicedReview(BaseModel):
    id: str
    topic_id: str
    status: Status
    overall: Optional["SlicedOverallReview"] = PydanticField(default=None)
    answers: list["SlicedAnswerReview"] = PydanticField(default=[])
    created_at: datetime


class SlicedOverallReview(BaseModel):
    id: str
    review_id: str

    score_range: Optional[tuple[int, int]] = PydanticField(default=None)
    level_achieved: Optional[int] = PydanticField(default=None)
    overall_feedback: Optional[str] = PydanticField(default=None)
    summary_feedback: Optional[str] = PydanticField(default=None)
    detail_score: Optional[DetailScore] = PydanticField(default=None)
    annotations: Optional[list[Annotation]] = PydanticField(default=None)
    improvement_suggestions: Optional[list[str]] = PydanticField(default=None)


class SlicedAnswerReview(BaseModel):  # For P1
    id: str
    review_id: str
    answer_id: str

    overall_score: int
    feedback: str
    details: P1DetailScore
    annotations: list[Annotation]


class Session(SQLModel, table=True):
    __tablename__ = "session"  # type: ignore

    id: str = SQLField(primary_key=True, default_factory=lambda: uuid4().__str__())

    started_at: datetime
    ended_at: datetime

    created_at: datetime = SQLField(default_factory=lambda: datetime.now())


class Statistics(BaseModel):
    total_submission: int
    total_topic: int
    average_score: float
    total_time: int
