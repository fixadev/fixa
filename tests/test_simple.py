from fixa import Test, Agent, Scenario, Evaluation, TestRunner

jessica = Agent(
    prompt="you are a young woman named lily who says 'like' a lot",
    voice_id="jessica",
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

test_runner = TestRunner(
    port=8765,
    ngrok_url="https://XXX.ngrok.dev",
    twilio_phone_number="+16508859164",
)

test_runner.add_test(test)
test_runner.run_tests(type=TestRunner.OUTBOUND, phone_number="+16508859164")
