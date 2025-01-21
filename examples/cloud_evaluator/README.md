# cloud evaluator

this example shows how to run a simple test with the `CloudEvaluator`

using the cloud evaluator gives you a link to the call analysis performed by fixa-observe

```bash
🎯 order_donut (jessica)
🔊 Recording URL: https://api.twilio.com/XXX
🔗 fixa-observe call analysis: https://www.fixa.dev/observe/calls/XXX
-- ❌ price_confirmed: Agent did not confirm the price for the donuts and coffee order.
-- ✅ order_success: Agent successfully confirmed the order of a dozen donuts and a coffee.
```

fixa-observe comes with an audio player, a transcript, and pinpoints where the evaluations failed. it also analyzes latency and interruptions.

the call analysis UI looks like this:

![fixa observe](../../.github/assets/fixa-observe.png)

## get started

1. create an account at https://fixa.dev

2. get your fixa API key from the API keys tab

<img src="../../.github/assets/api-keys.png" alt="api-keys" width="400"/>

3. run the following code

```python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # and add your credentials
```

4. add your fixa API key to the `.env` file

## run example

```python
python main.py
```
