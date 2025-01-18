from twilio.rest import Client
import os
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse

load_dotenv(override=True)

client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

response = VoiceResponse()
response.hangup()

client.calls("CA111289b1e0c8163667a65fda88d5e831").update(
    # twiml=response.to_xml(),
    status="canceled",
)
