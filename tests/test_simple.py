from fixa import Test, Agent, Scenario, Evaluation, TestRunner
from fixa.evaluators import LocalEvaluator
import ngrok
import os
from dotenv import load_dotenv
import asyncio

load_dotenv(override=True)

jessica = Agent(
    prompt="you are a young woman named lily who says 'like' a lot",
    voice_id="b7d50908-b17c-442d-ad8d-810c63997ed9"
)

order_donut = Scenario(
    name="order_donut",
    prompt="order a dozen donuts with sprinkles and a coffee",
    evaluations=[
        Evaluation(name="order_success", prompt="the order was successful"),
        Evaluation(name="price_confirmed", prompt="the agent confirmed the price of the order"),
    ],
)

tests = []
test = Test(order_donut, jessica)

port = 8765
listener = ngrok.forward(port, authtoken=os.getenv("NGROK_AUTH_TOKEN"), domain="api.jpixa.ngrok.dev")

test_runner = TestRunner(
    port=port,
    ngrok_url=listener.url(),
    twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER") or "",
    evaluator=LocalEvaluator(),
)

test_runner.add_test(test)
asyncio.run(test_runner.run_tests(type=TestRunner.OUTBOUND, phone_number=os.getenv("TEST_PHONE_NUMBER") or ""))
