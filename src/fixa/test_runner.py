import subprocess
import time
import requests
from fixa.test import Test
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv(override=True)
REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "DEEPGRAM_API_KEY", "CARTESIA_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "NGROK_AUTH_TOKEN"]

class TestRunner:
    INBOUND = "inbound"
    OUTBOUND = "outbound"

    def __init__(self, port: int, ngrok_url: str, twilio_phone_number: str):
        """
        Args:
            port: The port to run the server on.
            ngrok_url: The URL to use for ngrok.
            twilio_phone_number: The phone number to use as the "from" number for outbound test calls.
        """
        # Check that all required environment variables are set
        for env_var in REQUIRED_ENV_VARS:
            if env_var not in os.environ:
                raise Exception(f"Missing environment variable: {env_var}.")
        
        # Initialize instance variables
        self.port = port
        self.ngrok_url = ngrok_url
        self.twilio_phone_number = twilio_phone_number
        self.tests: list[Test] = []
        self.twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

    def add_test(self, test: Test):
        """
        Adds a test to the test runner.
        """
        self.tests.append(test)

    def run_tests(self, type: str, phone_number: str):
        """
        Runs all the tests that were added to the test runner.
        Args:
            type: The type of test to run. Can be TestRunner.INBOUND or TestRunner.OUTBOUND.
            phone_number: The phone number to call (for outbound tests).
        """
        self._start_server()

        for test in self.tests:
            if type == self.INBOUND:
                self._run_inbound_test(test, phone_number)
            elif type == self.OUTBOUND:
                self._run_outbound_test(test, phone_number)
            else:
                raise ValueError(f"Invalid test type: {type}. Must be TestRunner.INBOUND or TestRunner.OUTBOUND.")

        # Wait for tests to finish
        # TODO

        # self.server_process.terminate()
        assert self.server_process.stderr is not None
        while True:
            line = self.server_process.stderr.readline()
            print(line, end='')
            if "Application startup complete" in line:
                break
            if self.server_process.poll() is not None:
                break

        print("Server exited")

    def _start_server(self):
        """
        Starts the server.
        """
        server_path = os.path.join(os.path.dirname(__file__), "test_server.py")
        self.server_process = subprocess.Popen(
            ["python", server_path, "--port", str(self.port), "--ngrok_url", self.ngrok_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        self._wait_for_server()
        print("Server started...")

    def _wait_for_server(self):
        """
        Waits for the server to start.
        """
        assert self.server_process.stderr is not None

        while True:
            line = self.server_process.stderr.readline()
            print(line, end='')
            if "Application startup complete" in line:
                break
            if self.server_process.poll() is not None:
                raise Exception("Server failed to start")

    def _run_outbound_test(self, test: Test, phone_number: str):
        """
        Runs an outbound test.
        Args:
            test: The test to run.
            phone_number: The phone number to call.
        """
        print(f"\nRunning test: {test.scenario.name}")
        response = requests.post(f"{self.ngrok_url}/outbound", json={
            "to": phone_number,
            "from": self.twilio_phone_number,
            "scenario_prompt": test.scenario.prompt,
            "agent_prompt": test.agent.prompt,
            "agent_voice_id": test.agent.voice_id,
        })
        print(response.json())

    def _run_inbound_test(self, test: Test, phone_number: str):
        """
        Runs an inbound test.
        """
        raise NotImplementedError("Inbound tests are not implemented yet")