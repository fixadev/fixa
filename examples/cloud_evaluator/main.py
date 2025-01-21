from fixa import Test, Agent, Scenario, Evaluation, TestRunner
from fixa.evaluators import CloudEvaluator
from dotenv import load_dotenv
import ngrok, os, asyncio

load_dotenv(override=True)

TWILIO_PHONE_NUMBER = "+15554443333" # the twilio phone number to initiate calls from
PHONE_NUMBER_TO_CALL = "+15554443333" # the phone number to call

async def main():
    # define test agent to call your voice agent
    agent = Agent(
        name="jessica",
        prompt="you are a young woman named jessica who says 'like' a lot",
        voice_id="b7d50908-b17c-442d-ad8d-810c63997ed9"
    )

    # define a scenario to test
    scenario = Scenario(
        name="order_donut",
        prompt="order a dozen donuts with sprinkles and a coffee",
        # define evaluations to evaluate the scenario after it finishes running
        evaluations=[
            Evaluation(name="order_success", prompt="the order was successful"),
            Evaluation(name="price_confirmed", prompt="the agent confirmed the price of the order"),
        ],
    )

    # start an ngrok server so twilio can access your local websocket endpoint
    port = 8765
    listener = await ngrok.forward(port, authtoken=os.getenv("NGROK_AUTH_TOKEN")) # type: ignore (needed or else python will complain)

    # initialize a test runner
    test_runner = TestRunner(
        port=port,
        ngrok_url=listener.url(),
        twilio_phone_number=TWILIO_PHONE_NUMBER, 
        evaluator=CloudEvaluator(api_key=os.getenv("FIXA_API_KEY") or ""),
    )

    # add tests to the test runner
    test = Test(scenario=scenario, agent=agent)
    test_runner.add_test(test)

    # run the tests!
    test_results = await test_runner.run_tests(
        phone_number=PHONE_NUMBER_TO_CALL,
        type=TestRunner.OUTBOUND,
    )
    # print(test_results)

if __name__ == "__main__":
    asyncio.run(main())
