from fixa import Test, Agent, Scenario, Evaluation

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
test.run()