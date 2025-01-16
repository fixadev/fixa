from fixa import Test, Agent, Scenario

jessica = Agent(
    prompt="you are a young woman named lily who says 'like' a lot",
    model="gpt-4o",
    voice="jessica",
)

order_donut = Scenario(
    prompt="order a dozen donuts with sprinkles and a coffee",
    evaluations=[
        "the order was successful",
        "the agent confirmed the price of the order",
    ],
)

tests = []
test = Test(order_donut, jessica)
test.run()