from openai.types.chat import ChatCompletionMessageParam
from typing import List
import asyncio
from dotenv import load_dotenv

from fixa.evaluation import Evaluation
from fixa.evaluators import LocalEvaluator
from fixa.scenario import Scenario

load_dotenv(override=True)

async def test_evaluator():
    order_donut = Scenario(
        name="order_donut",
        prompt="order a dozen donuts with sprinkles and a coffee",
        evaluations=[
            Evaluation(name="order_success", prompt="the order was successful"),
            Evaluation(name="price_confirmed", prompt="the agent confirmed the price of the order"),
        ],
    )
    transcript: List[ChatCompletionMessageParam] = [
        {"role": "system", "content": "you are a young woman named jessica who says 'like' a lot"},
        {"role": "system", "content": "order a dozen donuts with sprinkles and a coffee"},
        {"role": "system", "content": "end the call if the user says goodbye"},
        {"role": "system", "content": "your first response should be an empty string. nothing else."},
        {"role": "user", "content": "Hello. This is Oliver Stone. How can I help you today?"},
        {"role": "assistant", "content": "Um, like, hi Oliver! I was, like, wondering if I could get, like, a dozen donuts with sprinkles and, like, a coffee, please?"},
        {"role": "user", "content": "Yeah. Sure. Dozen donuts and a coffee."},
        {"role": "assistant", "content": "Awesome! Thanks a bunch, Oliver. Like, can't wait to get them!"},
        {"role": "user", "content": "Alright. Goodbye."}
    ]
    stereo_recording_url = ""
    evaluator = LocalEvaluator()
    evaluation_results = await evaluator.evaluate(order_donut, transcript, stereo_recording_url)
    print(evaluation_results)

if __name__ == "__main__":
    asyncio.run(test_evaluator())
