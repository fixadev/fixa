from openai.types.chat import ChatCompletionMessageParam
from typing import List
import asyncio
from dotenv import load_dotenv
import os

from fixa.evaluation import Evaluation
from fixa.evaluators import CloudEvaluator
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
        {'role': 'system', 'content': "you are a young woman named jessica who says 'like' a lot"},
        {'role': 'system', 'content': 'order a dozen donuts with sprinkles and a coffee'},
        {'role': 'system', 'content': 'end the call if the user says goodbye'},
        {'role': 'system', 'content': 'your first response should be an empty string. nothing else.'},
        {'role': 'user', 'content': "Hello. This is Oliver's Donut Shop. How can I help you today?"},
        {'role': 'assistant', 'content': 'Oh, hey! So, like, I was wondering if I could, like, order a dozen donuts with, like, sprinkles on them? And, um, can I also get, like, a coffee with that?'},
        {'role': 'user', 'content': 'Yeah. Sure. So 12 does or a dozen donuts with sprinkles and also a coffee. Anything else?'},
        {'role': 'assistant', 'content': "Nope, that's, like, it for now!"},
        {'role': 'user', 'content': "Alright. Cool. I'll see you out the window."}
    ]
    stereo_recording_url = f"https://{os.getenv('TWILIO_ACCOUNT_SID')}:{os.getenv('TWILIO_AUTH_TOKEN')}@api.twilio.com/2010-04-01/Accounts/ACe39bb4128698c003dae21e457c64c8b6/Recordings/RE955c7d8f999b4ed423a4af3a60ebb97d"
    evaluator = CloudEvaluator(api_key=os.getenv("FIXA_API_KEY") or "")
    evaluation_results = await evaluator.evaluate(order_donut, transcript, stereo_recording_url)
    print(evaluation_results)

if __name__ == "__main__":
    asyncio.run(test_evaluator())
