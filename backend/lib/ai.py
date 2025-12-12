import json
from typing import Literal, cast

import openrouter
from pydantic import ValidationError
from sqlmodel import SQLModel

from .env import (
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    QUESTION_MODEL,
    REVIEW_MODEL,
    SUMMARY_MODEL,
)

client = openrouter.OpenRouter(api_key=OPENROUTER_API_KEY, server_url=OPENROUTER_URL)

system_prompt_for_topic_p2 = ""
system_prompt_for_topic_p3 = ""
system_prompt_for_review = ""
system_prompt_for_summary = ""
base_user_prompt_for_topic = ""
base_user_prompt_for_submit = ""
base_fix_json_request = ""

with open("assets/topic/part_2.txt") as file:
    system_prompt_for_topic_p2 = file.read()

with open("assets/topic/part_3.txt") as file:
    system_prompt_for_topic_p3 = file.read()

with open("assets/submit/part_2_3/system.txt") as file:
    system_prompt_for_review = file.read()

with open("assets/submit/part_2_3/summary.txt") as file:
    system_prompt_for_summary = file.read()

with open("assets/topic/user.txt") as file:
    base_user_prompt_for_topic = file.read()

with open("assets/submit/part_2_3/user.txt") as file:
    base_user_prompt_for_submit = file.read()

with open("assets/error.txt") as file:
    base_fix_json_request = file.read()

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


async def generate_topic(part: Literal["2"] | Literal["3"]):
    return str(
        (
            await client.chat.send_async(
                model=QUESTION_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt_for_topic_p2
                        if part == "2"
                        else system_prompt_for_topic_p3,
                    },
                    {
                        "role": "user",
                        "content": base_user_prompt_for_topic.format(part=part),
                    },
                ],
            )
        )
        .choices[0]
        .message.content
    )


async def summary(topic: str):
    for _ in range(5):
        response = str(
            (
                await client.chat.send_async(
                    model=SUMMARY_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt_for_summary,
                        },
                        {
                            "role": "user",
                            "content": topic,
                        },
                    ],
                )
            )
            .choices[0]
            .message.content
        )

        sliced = slice_md(str(response))

        try:
            parsed_summary = json.loads(sliced)
            return SummaryResponse(**parsed_summary)

        except (json.decoder.JSONDecodeError, ValidationError) as error:
            print(error)


async def review(part: Literal["2"] | Literal["3"], topic: str, submission: str):
    old_response: str = ""
    for _ in range(5):
        response = (
            (
                await client.chat.send_async(
                    model=REVIEW_MODEL,
                    messages=cast(
                        list[openrouter.components.Message],
                        filter(
                            lambda x: x is not None,
                            [
                                openrouter.components.SystemMessage(
                                    content=system_prompt_for_review
                                ),
                                openrouter.components.UserMessage(
                                    content=base_user_prompt_for_submit.format(
                                        part=part,
                                        topic=topic,
                                        submission=submission,
                                    )
                                ),
                                openrouter.components.UserMessage(
                                    content=base_user_prompt_for_submit.format(
                                        part=part,
                                        topic=topic,
                                        submission=submission,
                                    )
                                )
                                if old_response.__len__()
                                else None,
                            ],
                        ),
                    ),
                    temperature=0.5,
                )
            )
            .choices[0]
            .message.content
        )
        sliced = slice_md(str(response))

        try:
            parsed_review = json.loads(sliced)
            return ReviewResponse(**parsed_review)

        except (json.decoder.JSONDecodeError, ValidationError) as error:
            print(error)
            old_response = sliced
            print("\n---\n")
            continue

    return None

def slice_md(text: str):
    if text.startswith("```json"):
        text = text[7:]
    
    if text.startswith("```"):
        text = text[4:]

    if text.endswith("```"):
        text = text[:-3]
    
    return text
