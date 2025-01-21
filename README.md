<h1>
<div align="center">
  <img alt="fixa logo" width="300px" height="auto" src="https://raw.githubusercontent.com/fixadev/fixa/main/.github/assets/logo.png">
</div>
</h1>

[![PyPI](https://img.shields.io/pypi/v/fixa-dev)](https://pypi.org/project/fixa-dev) [![Docs](https://img.shields.io/badge/documentation-white)](https://docs.fixa.dev) [![discord](https://img.shields.io/badge/join-discord-blue)](https://discord.gg/rT9cYkfybZ)

fixa is a python package for testing and evaluating AI voice agents.

it uses a voice agent to call your voice agent and an LLM to evaluate how the conversation went.

under the hood, this package uses:

- [Pipecat](https://github.com/pipecat-ai/pipecat) for the agent
- Cartesia for TTS
- Deepgram for transcription
- OpenAI for the evaluator
- Twilio to initiate calls

(other integrations coming soon)

## demo

[![demo video](http://markdown-videos-api.jorgenkh.no/youtube/LAW1wW6SjTo)](https://www.youtube.com/watch?v=LAW1wW6SjTo)

## quick start

### installation:

```bash
pip install fixa-dev
```

### set up your environment variables in a `.env` file

```bash
OPENAI_API_KEY=
DEEPGRAM_API_KEY=
CARTESIA_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
NGROK_AUTH_TOKEN=
```

### run a test:

make sure to replace `TWILIO_PHONE_NUMBER` and `PHONE_NUMBER_TO_CALL` with your own numbers.

if you have a paid ngrok plan, be sure to add your ngrok domain to the `listener` variable.

```python
from fixa import Test, Agent, Scenario, Evaluation, TestRunner
from fixa.evaluators import LocalEvaluator
from dotenv import load_dotenv
import ngrok, os, asyncio

load_dotenv(override=True)

TWILIO_PHONE_NUMBER = "+15554443333" # the twilio phone number to initiate calls from (must be a number you own)
PHONE_NUMBER_TO_CALL = "+15554443333" # the phone number of your agent

async def main():
    # define test agent to call your voice agent
    agent = Agent(
        name="jessica",
        prompt="you are a young woman named jessica who says 'like' a lot",
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
    # uncomment the line below if you have a paid ngrok plan (need to specify a domain)
    listener = await ngrok.forward(port, authtoken=os.getenv("NGROK_AUTH_TOKEN")) # type: ignore (needed or else python will complain)
    # listener = await ngrok.forward(port, authtoken=os.getenv("NGROK_AUTH_TOKEN"), domain="your_domain.ngrok.dev") # type: ignore (needed or else python will complain)

    # initialize a test runner
    test_runner = TestRunner(
        port=port,
        ngrok_url=listener.url(),
        twilio_phone_number=TWILIO_PHONE_NUMBER,
        evaluator=LocalEvaluator(),
    )

    # add tests to the test runner
    test = Test(scenario=scenario, agent=agent)
    test_runner.add_test(test)

    # run the tests!
    test_results = await test_runner.run_tests(
        phone_number=PHONE_NUMBER_TO_CALL,
        type=TestRunner.OUTBOUND,
    )

if __name__ == "__main__":
    asyncio.run(main())

```

### view the results

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

for more info, check out our [docs](https://docs.fixa.dev)

for questions setting anything up, [join our discord](https://discord.gg/rT9cYkfybZ)

## how it works

### 1. define agents and scenarios

agents are the voice agents that will call your voice agent. give each agent a prompt which determines its characteristics, like speaking patterns or personality.

```python
agent = Agent(
    name="jessica",
    prompt="you are a young woman named jessica who says 'like' a lot",
)
```

scenarios are the situations in which you would like to test your voice agent. give each scenario a prompt for how the test agent should act when calling your voice agent. also add some evaluations that will determine how the call will be evaluated after the scenario finishes running.

```python
scenario = Scenario(
    name="order_donut",
    prompt="order a dozen donuts with sprinkles and a coffee",
    # define evaluations to evaluate the scenario after it finishes running
    evaluations=[
        Evaluation(name="order_success", prompt="the order was successful"),
        Evaluation(name="price_confirmed", prompt="the agent confirmed the price of the order"),
    ],
)
```

### 2. define tests

a test is an association between the scenario to run and which agent to use.

```python
test = Test(scenario=scenario, agent=agent)
```

### 3. create a test runner

a test runner is used to actually execute the tests.

```python
test_runner = TestRunner(
    port=port,
    ngrok_url=listener.url(),
    twilio_phone_number="+15554443333", # the twilio phone number to initiate calls from
    evaluator=LocalEvaluator(),
)
test_runner.add_test(test)
test_results = await test_runner.run_tests(
    type=TestRunner.OUTBOUND,
    phone_number="+15554443333", # the phone number to call
)
```

when tests are run, all the test calls are made simultaneously to the phone number provided, with the voice agent executing the prompt instructions specified in the scenario.

### 4. get results

after a call finishes, the evaluations defined as part of the scenario are run on the transcript, and the results are printed to the terminal.

```bash
🎯 order_donut (jessica)
🔊 Recording URL: https://api.twilio.com/XXX
-- ✅ order_success: The order was successfully placed and confirmed by the user and the assistant.
-- ❌ price_confirmed: The price of the order was not mentioned or confirmed during the conversation.
```

more information including transcript, etc. is available in the `test_results` object that is returned by the `run_tests()` function.

## visualize the results

if you would like to visualize the results in a UI rather than in code, use the `CloudEvaluator`, which uploads the call to fixa observe. [sign up here](https://fixa.dev)

```python
from fixa.evaluators import CloudEvaluator
test_runner = TestRunner(
    port=port,
    ngrok_url=listener.url(),
    twilio_phone_number="+15554443333", # the twilio phone number to initiate calls from
    evaluator=CloudEvaluator(api_key=os.getenv("FIXA_API_KEY") or ""),
)
```

[see a full example here](./examples/cloud_evaluator)

fixa observe comes with an audio player, a transcript, and pinpoints where the evaluations failed. it also analyzes latency and interruptions.

![fixa observe](./.github/assets/fixa-observe.png)
