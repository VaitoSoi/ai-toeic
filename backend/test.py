import asyncio

from lib.ai import review


async def main():
    review_ = await review(
        "2",
        """Many companies are encouraging their employees to spend time on volunteer work in the local community (e.g., teaching children, planting trees, helping elderly citizens). Some people believe this practice is highly beneficial for both the employee and the company. Others argue that mandatory volunteering is an unfair demand on employees and distracts from core business activities.

Do you agree or disagree that companies should strongly encourage, and potentially require, employees to participate in community volunteer work? Use specific reasons and examples to support your position.""",
"""
In today's world, where kindness and connectivity is being prioritized, volunteering is not only benefit who is helped but also who is giving the hand. Volunteer work helps create connection not only between society and company but also among employees. Consequently, it increase company social recognition.
Firstly, volunteer creates connection among people. Volunteer work helps enployees reach people, who are in poverty or difficult circumstances. Therefore, it emphasizes conpassion in each person. On the other hand, it help develop soft skill, for instance, team-work, which is crucial in a professional environment.
In addition, volunteering increase social recognition of the company. Society supporting event usually attract a lot of people, thereby marketing the company image to the public. Take Cocoon as an instance. They have made a lot of volunteer programs for not only poverty people, highlander but also animal. This raise the community awareness about the modern world problem. The programs are also strongly attached with the company product, thereby attract new customers.
In conclusion, volunteer work is beneficial for both society and company. Thereby, volunteering should be encouraged for a better society
"""
    )
    if (review_):
        print(review_.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
