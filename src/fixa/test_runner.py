import subprocess
from typing import Dict, List, Optional
import requests
import os
from dotenv import load_dotenv
from twilio.rest import Client
import asyncio

from fixa.test import Test
from fixa.evaluators import BaseEvaluator, EvaluationResult
from fixa.test_server import CallStatus

load_dotenv(override=True)
REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "DEEPGRAM_API_KEY", "CARTESIA_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "NGROK_AUTH_TOKEN"]

class TestRunner:
    INBOUND = "inbound"
    OUTBOUND = "outbound"

    def __init__(self, port: int, ngrok_url: str, twilio_phone_number: str, evaluator: BaseEvaluator | None = None):
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
        self.evaluator = evaluator
        self.tests: list[Test] = []

        self._twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        self._status: Dict[str, CallStatus] = {}
        self._call_id_to_test: Dict[str, Test] = {}
        self._evaluation_results: Dict[str, List[EvaluationResult]] = {}

    def add_test(self, test: Test):
        """
        Adds a test to the test runner.
        """
        self.tests.append(test)

    async def run_tests(self, type: str, phone_number: str):
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

        evaluated_calls = set()
        assert self.server_process.stderr is not None

        async with asyncio.TaskGroup() as tg:
            while len(evaluated_calls) < len(self.tests):
                response = requests.get(f"{self.ngrok_url}/status")
                self._status = response.json()
                print("STATUS", self._status, flush=True)

                # Check each call status and evaluate if complete
                for call_id, status in self._status.items():
                    if (
                        call_id not in evaluated_calls
                        and status["status"] == "completed"
                        and status["transcript"] is not None
                        and status["stereo_recording_url"] is not None
                    ):
                        evaluated_calls.add(call_id)
                        tg.create_task(self._evaluate_call(call_id))

                await asyncio.sleep(1)

        # All tests are complete, stop the server
        self.server_process.terminate()
        print("All tests completed, server stopped")
        print(self._call_id_to_test)
        print(self._status)
        print(self._evaluation_results)

    async def _evaluate_call(self, call_id: str) -> Optional[List[EvaluationResult]]:
        """
        Evaluates a call.
        """
        call_status = self._status[call_id]
        test = self._call_id_to_test[call_id]
        if (
            call_status["transcript"] is None
            or call_status["stereo_recording_url"] is None
            or test is None
            or self.evaluator is None
        ):
            return

        evaluation_results = await self.evaluator.evaluate(test.scenario, call_status["transcript"], call_status["stereo_recording_url"])
        if evaluation_results is not None:
            self._evaluation_results[call_id] = evaluation_results
        return evaluation_results

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
        print("Server started...", flush=True)

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
        self._call_id_to_test[response.json()["call_id"]] = test

    def _run_inbound_test(self, test: Test, phone_number: str):
        """
        Runs an inbound test.
        """
        raise NotImplementedError("Inbound tests are not implemented yet")