# fixa

a tool for testing and evaluating AI voice agents.

use a voice agent to call your voice agent with an llm as a judge.

# quick start

with pip:

```bash
pip install fixa-dev
```

run a test:

```python
from fixa import Test, Agent, Scenario, Evaluation, TestRunner
from fixa.evaluators import LocalEvaluator
from dotenv import load_dotenv
import ngrok, os, asyncio

load_dotenv(override=True)

async def main():
    agent = Agent(
        name="jessica",
        prompt="you are a young woman named lily who says 'like' a lot",
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
        twilio_phone_number="+15554443333", # the twilio phone number to initiate calls from
        evaluator=LocalEvaluator(),
    )

    test = Test(scenario=scenario, agent=agent)
    test_runner.add_test(test)

    result = await test_runner.run_tests(
        type=TestRunner.OUTBOUND,
        phone_number="+15554443333", # the phone number to call
    )

if __name__ == "__main__":
    asyncio.run(main())

```

make sure to add the following api keys to your `.env` file:

```bash
OPENAI_API_KEY=
DEEPGRAM_API_KEY=
CARTESIA_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
NGROK_AUTH_TOKEN=
```

example output in the console:

```bash
✨ All tests completed!

📊 Test Results:
==================================================

🎯 order_donut (jessica)
🔊 Recording URL: https://api.twilio.com/XXX
-- ✅ order_success: The order was successfully placed and confirmed by the user and the assistant.
-- ❌ price_confirmed: The price of the order was not mentioned or confirmed during the conversation.

==================================================
```

for more info, check out our docs

for questions setting anything up, join our discord
