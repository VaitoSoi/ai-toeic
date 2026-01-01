import json
from typing import Literal, Optional

from aiohttp import ClientSession
from pydantic import BaseModel, Field, ValidationError
from sqlmodel import SQLModel

from .env import (
    ARTIST_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    QUESTION_MODEL,
    REVIEW_MODEL,
    SUMMARY_MODEL,
)

client: ClientSession


def init():
    global client
    client = ClientSession(
        base_url=OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
    )


system_prompt_for_topic_p1 = ""
system_prompt_for_topic_p2 = ""
system_prompt_for_topic_p3 = ""
system_prompt_for_review_1 = ""
system_prompt_for_review_2_3 = ""
system_prompt_for_summary_2_3 = ""
base_user_prompt_for_topic = ""
base_user_prompt_for_submit_1 = ""
base_user_prompt_for_submit_2_3 = ""
base_fix_json_request = ""

with open("assets/topic/part_1.txt") as file:
    system_prompt_for_topic_p1 = file.read()

with open("assets/topic/part_2.txt") as file:
    system_prompt_for_topic_p2 = file.read()

with open("assets/topic/part_3.txt") as file:
    system_prompt_for_topic_p3 = file.read()

with open("assets/submit/part_1/system.txt") as file:
    system_prompt_for_review_1 = file.read()

with open("assets/submit/part_2_3/system.txt") as file:
    system_prompt_for_review_2_3 = file.read()

with open("assets/submit/part_2_3/summary.txt") as file:
    system_prompt_for_summary_2_3 = file.read()

with open("assets/topic/user.txt") as file:
    base_user_prompt_for_topic = file.read()

with open("assets/submit/part_2_3/user.txt") as file:
    base_user_prompt_for_submit_2_3 = file.read()

with open("assets/error.txt") as file:
    base_fix_json_request = file.read()


class MessageImageUrlData(BaseModel):
    url: str


class MessageContentText(BaseModel):
    type: Literal["text"]
    text: str


class MessageContentImage(BaseModel):
    type: Literal["image_url"]
    image_url: MessageImageUrlData


class BaseUserMessage(BaseModel):
    role: Literal["user", "system"]
    content: str


class BaseRequest(BaseModel):
    model: str
    messages: list[BaseUserMessage] | str
    stream: bool = Field(default=False)


class BaseReponseMessage(BaseModel):
    role: Literal["assistant"]
    content: str
    images: Optional[list[MessageContentImage]] = Field(default=None)


class BaseReponseChoice(BaseModel):
    index: int
    message: BaseReponseMessage


class BaseReponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list[BaseReponseChoice]


class TopicP1Response(BaseModel):
    artist_prompt: str
    keywords: tuple[str, str]


class SummaryResponse(SQLModel):
    summary: str
    description: str


class ReviewResponse(SQLModel):
    score_range: tuple[int, int]
    level_achieved: int
    overall_feedback: str
    summary_feedback: str
    detail_score: "DetailScore"
    annotations: list["Annotation"]
    improvement_suggestions: list[str]


class DetailScore(SQLModel):
    grammar: int
    vocabulary: int
    organization: int
    task_fulfillment: int


class Annotation(SQLModel):
    target_text: str
    context_before: str
    type: (
        Literal["grammar"]
        | Literal["vocabulary"]
        | Literal["coherence"]
        | Literal["mechanics"]
    )
    replacement: str | None
    feedback: str


def format_message(messages: list[BaseUserMessage]):
    return [message.model_dump() for message in messages]


async def generate_topic_p1():
    for _ in range(5):
        response = await client.post(
            url="/proxy/v1/chat/completions",
            json=BaseRequest(
                model=QUESTION_MODEL,
                messages=[
                    BaseUserMessage(role="system", content=system_prompt_for_topic_p1),
                    BaseUserMessage(
                        role="user",
                        content=base_user_prompt_for_topic.format(part="1"),
                    ),
                ],
            ).model_dump(),
        )
        data = BaseReponse(**(await response.json()))

        sliced = slice_md(data.choices[0].message.content)

        try:
            parsed_topic = json.loads(sliced)
            return TopicP1Response(**parsed_topic)

        except (json.decoder.JSONDecodeError, ValidationError) as error:
            print(error)


async def generate_topic_p2_3(part: Literal["2", "3"]):
    response = await client.post(
        url="/proxy/v1/chat/completions",
        json=BaseRequest(
            model=QUESTION_MODEL,
            messages=[
                BaseUserMessage(
                    role="system",
                    content=system_prompt_for_topic_p2
                    if part == "2"
                    else system_prompt_for_topic_p3,
                ),
                BaseUserMessage(
                    role="user",
                    content=base_user_prompt_for_topic.format(part=part),
                ),
            ],
        ).model_dump(),
    )
    data = BaseReponse(**(await response.json()))
    return data.choices[0].message.content


async def generate_image(prompt: str):
    response = await client.post(
        url="/proxy/v1/chat/completions",
        json=BaseRequest(
            model=ARTIST_MODEL,
            messages=[
                BaseUserMessage(
                    role="user",
                    content=prompt,
                ),
            ],
        ).model_dump(),
    )
    data = BaseReponse(**(await response.json()))
    return (
        data.choices[0].message.images[0].image_url.url
        if data.choices[0].message.images
        else None
    )


async def summary(topic: str):
    for _ in range(5):
        response = await client.post(
            url="/proxy/v1/chat/completions",
            json=BaseRequest(
                model=SUMMARY_MODEL,
                messages=[
                    BaseUserMessage(
                        role="system", content=system_prompt_for_summary_2_3
                    ),
                    BaseUserMessage(role="user", content=topic),
                ],
            ).model_dump(),
        )
        data = BaseReponse(**(await response.json()))

        sliced = slice_md(data.choices[0].message.content)

        try:
            parsed_summary = json.loads(sliced)
            return SummaryResponse(**parsed_summary)

        except (json.decoder.JSONDecodeError, ValidationError) as error:
            print(error)

    return None


async def review(part: Literal["1", "2", "3"], topic: str, submission: str):
    for _ in range(5):
        response = await client.post(
            url="/proxy/v1/chat/completions",
            json=BaseRequest(
                model=REVIEW_MODEL,
                messages=[
                    BaseUserMessage(
                        role="system", content=system_prompt_for_review_2_3
                    ),
                    BaseUserMessage(
                        role="user",
                        content=base_user_prompt_for_submit_2_3.format(
                            part=part,
                            topic=topic,
                            submission=submission,
                        ),
                    ),
                ],
            ).model_dump(),
        )
        data = BaseReponse(**(await response.json()))
        sliced = slice_md(data.choices[0].message.content)

        try:
            parsed_review = json.loads(sliced)
            return ReviewResponse(**parsed_review)

        except (json.decoder.JSONDecodeError, ValidationError) as error:
            print(error)

    return None


def slice_md(text: str):
    if text.startswith("```json"):
        text = text[7:]

    if text.startswith("```"):
        text = text[4:]

    if text.endswith("```"):
        text = text[:-3]

    return text
