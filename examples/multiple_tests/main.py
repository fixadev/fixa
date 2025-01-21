from fixa import Test, Agent, Scenario, Evaluation, TestRunner
from fixa.evaluators import LocalEvaluator
from dotenv import load_dotenv
import ngrok, os, asyncio

load_dotenv(override=True)

TWILIO_PHONE_NUMBER = "+15554443333" # the twilio phone number to initiate calls from
PHONE_NUMBER_TO_CALL = "+15554443333" # the phone number to call

async def main():
    # define test agents to call your voice agent
    agents = [
        Agent(
            name="jessica",
            prompt="you are a young woman named jessica who says 'like' a lot",
            voice_id="b7d50908-b17c-442d-ad8d-810c63997ed9"
        ),
        Agent(
            name="steve",
            prompt="you are a man named steve who had a bad day at work and is now angry",
            voice_id="95856005-0332-41b0-935f-352e296aa0df"
        ),
        Agent(
            name="marge",
            prompt="you are an elderly woman named marge who sometimes gets carried away",
        ),
    ]

    # define scenarios to test
    scenarios = [
        Scenario(
            name="order_donut",
            prompt="order a dozen donuts with sprinkles and a coffee",
            evaluations=[
            Evaluation(name="order_success", prompt="the order was successful"),
                Evaluation(name="price_confirmed", prompt="the agent confirmed the price of the order"),
            ],
        ),
        Scenario(
            name="ask_question",
            prompt="ask a question about store hours",
            evaluations=[
                Evaluation(name="question_answered", prompt="the agent answered the question correctly and in a way that is helpful"),
            ],
        ),
        Scenario(
            name="ask_question_2",
            prompt="ask a question about the store's address",
            evaluations=[
                Evaluation(name="question_answered", prompt="the agent answered the question correctly and in a way that is helpful"),
            ],
        ),
    ]

    # start an ngrok server so twilio can access your local websocket endpoint
    port = 8765
    listener = await ngrok.forward(port, authtoken=os.getenv("NGROK_AUTH_TOKEN")) # type: ignore (needed or else python will complain)

    # initialize a test runner
    test_runner = TestRunner(
        port=port,
        ngrok_url=listener.url(),
        twilio_phone_number=TWILIO_PHONE_NUMBER, # the twilio phone number to initiate calls from
        evaluator=LocalEvaluator(),
    )

    # add tests to the test runner
    for scenario in scenarios:
        for agent in agents:
            test = Test(scenario=scenario, agent=agent)
            test_runner.add_test(test)

    # run the tests!
    test_results = await test_runner.run_tests(
        phone_number=PHONE_NUMBER_TO_CALL, # the phone number to call
        type=TestRunner.OUTBOUND, 
    )
    # print(test_results)

if __name__ == "__main__":
    asyncio.run(main())
