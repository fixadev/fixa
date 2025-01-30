from fixa import Test, Agent, Scenario, Evaluation, TestRunner
from fixa.evaluators import LocalEvaluator, CloudEvaluator
from dotenv import load_dotenv
import ngrok, os, asyncio

load_dotenv(override=True)

TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER") or ""
PHONE_NUMBER_TO_CALL = os.getenv("TEST_PHONE_NUMBER") or ""

async def main():
    agent = Agent(
        name="jessica",
        prompt="you are a young woman named jessica who says 'like' a lot",
        voice_id="b7d50908-b17c-442d-ad8d-810c63997ed9"
    )

    scenario = Scenario(
        name="order_donut",
        prompt="order a dozen donuts with sprinkles and a coffee",
        evaluations=[
            Evaluation(name="order_success", prompt="the order was successful"),
            Evaluation(name="price_confirmed", prompt="the agent confirmed the price of the order"),
        ],
    )

    port = 8765
    listener = await ngrok.forward(port, authtoken=os.getenv("NGROK_AUTH_TOKEN"), domain="api.jpixa.ngrok.dev") # type: ignore (needed or else python will complain)

    test_runner = TestRunner(
        port=port,
        ngrok_url=listener.url(),
        twilio_phone_number=TWILIO_PHONE_NUMBER,
        evaluator=LocalEvaluator(),
        # evaluator=CloudEvaluator(api_key=os.getenv("FIXA_API_KEY") or ""),
    )

    test = Test(scenario=scenario, agent=agent)
    test_runner.add_test(test)

    test_results = await test_runner.run_tests(
        phone_number=PHONE_NUMBER_TO_CALL,
        type=TestRunner.OUTBOUND,
    )

    print("test_results", test_results)

if __name__ == "__main__":
    asyncio.run(main())
