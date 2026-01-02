import json
from random import choice, choices
from typing import Any, Literal, Optional, Union

from aiohttp import ClientSession
from pydantic import BaseModel, Field, ValidationError
from sqlmodel import SQLModel

from .env import (
    ARTIST_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    QUESTION_MODEL,
    REVIEW_MODEL,
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


class BaseTheme(BaseModel):
    theme: str


class P1Theme(BaseTheme):
    subjects: list[str]
    actions: list[str]
    objects: list[str]


class P2Theme(BaseTheme):
    senders: list[str]
    recipients: list[str]
    problems: list[str]


class P3Theme(BaseTheme):
    opinions: list[str]
    keywords: list[str]


class Summary(SQLModel):
    summary: str
    description: str


class P1Response(BaseModel):
    artist_prompt: str
    keywords: tuple[str, str]


class P2ContentHeader(BaseModel):
    from_: str
    to: str
    subject: str
    sent: str


class P2Content(BaseModel):
    email_header: P2ContentHeader
    email_body: str
    direction: str


class P2Response(BaseModel):
    information: Summary
    test_content: P2Content


class P3Content(BaseModel):
    context_statement: str
    question_prompt: Optional[str] = Field(default=None)
    task_requirement: str


class P3Response(BaseModel):
    information: Summary
    test_content: P3Content


system_prompt_for_topic_p1 = ""
system_prompt_for_image_p1 = ""
system_prompt_for_topic_p2 = ""
system_prompt_for_topic_p3 = ""
themes_for_p1: list[P1Theme] = []
themes_for_p2: list[P2Theme] = []
themes_for_p3: list[P3Theme] = []
system_prompt_for_review_1 = ""
system_prompt_for_review_2_3 = ""
base_user_prompt_for_topic = ""
base_user_prompt_for_submit_1 = ""
base_user_prompt_for_submit_2_3 = ""
base_fix_json_request = ""

with open("assets/topic/p1/system.txt") as file:
    system_prompt_for_topic_p1 = file.read()

with open("assets/topic/p1/image.txt") as file:
    system_prompt_for_image_p1 = file.read()

with open("assets/topic/p1/theme.json") as file:
    raw_themes = json.load(file)
    themes_for_p1 = [P1Theme.model_validate(theme) for theme in raw_themes]

with open("assets/topic/p2/system.txt") as file:
    system_prompt_for_topic_p2 = file.read()

with open("assets/topic/p2/theme.json") as file:
    raw_themes = json.load(file)
    themes_for_p2 = [P2Theme.model_validate(theme) for theme in raw_themes]

with open("assets/topic/p3/system.txt") as file:
    system_prompt_for_topic_p3 = file.read()

with open("assets/topic/p3/theme.json") as file:
    raw_themes = json.load(file)
    themes_for_p3 = [P3Theme.model_validate(theme) for theme in raw_themes]

with open("assets/submit/p1/system.txt") as file:
    system_prompt_for_review_1 = file.read()

with open("assets/submit/p2_3/system.txt") as file:
    system_prompt_for_review_2_3 = file.read()

with open("assets/topic/user.txt") as file:
    base_user_prompt_for_topic = file.read()

with open("assets/submit/p2_3/user.txt") as file:
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


class BaseRequestFormat(BaseModel):
    type: Literal["json_object"]


class BaseRequest(BaseModel):
    model: str
    messages: list[BaseUserMessage] | str
    stream: bool = Field(default=False)
    response_format: Optional[BaseRequestFormat] = Field(default=None)


class ImageConfig(BaseModel):
    aspect_ratio: str


class BaseImageRequest(BaseRequest):
    modalities: list[str]
    image_config: Union[dict[str, Any], ImageConfig]


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


async def generate_image(prompt: str):
    response = await client.post(
        url="/proxy/v1/chat/completions",
        json=BaseImageRequest(
            model=ARTIST_MODEL,
            messages=[
                BaseUserMessage(role="system", content=system_prompt_for_image_p1),
                BaseUserMessage(
                    role="user",
                    content=prompt,
                ),
            ],
            modalities=["image"],
            image_config=ImageConfig(aspect_ratio="5:4"),
        ).model_dump(),
    )
    data = BaseReponse(**(await response.json()))
    return (
        data.choices[0].message.images[0].image_url.url
        if data.choices[0].message.images
        else None
    )


async def generate_topic(part: Literal["1", "2", "3"]):
    if part == "1":
        system_prompt = system_prompt_for_topic_p1
        theme = choice(themes_for_p1)
        subject = choice(theme.subjects)
        action = choice(theme.actions)
        object = choice(theme.objects)
        topic_theme = (
            f"**Subject:** {subject}\n**Action:** {action}\n**Object:** {object}"
        )
    elif part == "2":
        system_prompt = system_prompt_for_topic_p2
        theme = choice(themes_for_p2)
        sender = choice(theme.senders)
        recipient = choice(theme.recipients)
        problem = choice(theme.problems)
        topic_theme = (
            f"**Sender:** {sender}\n**Recipient:** {recipient}\n**Problem:** {problem}"
        )
    elif part == "3":
        system_prompt = system_prompt_for_topic_p3
        theme = choice(themes_for_p3)
        opinion = choice(theme.opinions)
        keywords = choices(theme.keywords, k=2)
        topic_theme = f"**Opinion:** {opinion}\n**Keywords:** {', '.join(keywords)}"

    for _ in range(5):
        response = await client.post(
            url="/proxy/v1/chat/completions",
            json=BaseRequest(
                model=QUESTION_MODEL,
                messages=[
                    BaseUserMessage(
                        role="system",
                        content=system_prompt,
                    ),
                    BaseUserMessage(
                        role="user",
                        content=base_user_prompt_for_topic.format(
                            part=part, theme=topic_theme
                        ),
                    ),
                ],
                response_format=BaseRequestFormat(type="json_object"),
            ).model_dump(),
        )

        data = BaseReponse(**(await response.json()))
        sliced = slice_md(data.choices[0].message.content)

        try:
            parsed_topic = json.loads(sliced)
            if part == "1":
                return P1Response.model_validate(parsed_topic)
            elif part == "2":
                return P2Response.model_validate(parsed_topic)
            elif part == "3":
                return P3Response.model_validate(parsed_topic)

        except (json.decoder.JSONDecodeError, ValidationError) as error:
            print(error)


async def review(part: Literal["1", "2", "3"], topic: str, submission: str):
    for _ in range(5):
        response = await client.post(
            url="/proxy/v1/chat/completions",
            json=BaseRequest(
                model=REVIEW_MODEL,
                messages=[
                    BaseUserMessage(role="system", content=system_prompt_for_review_2_3),
                    BaseUserMessage(
                        role="user",
                        content=base_user_prompt_for_submit_2_3.format(
                            part=part,
                            topic=topic,
                            submission=submission,
                        ),
                    ),
                ],
                response_format=BaseRequestFormat(type="json_object"),
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
