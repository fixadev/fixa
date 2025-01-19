import subprocess
from typing import Dict, List, Optional
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from twilio.rest import Client
import asyncio
import sys
from datetime import datetime
import aiohttp
from openai.types.chat import ChatCompletionMessageParam

from fixa import Scenario, Test
from fixa.evaluators import BaseEvaluator, EvaluationResult
from fixa.test_server import CallStatus

load_dotenv(override=True)
REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "DEEPGRAM_API_KEY", "CARTESIA_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "NGROK_AUTH_TOKEN"]

class TestResult():
    """
    Result of a test.
    """
    def __init__(self, test: Test, evaluation_results: List[EvaluationResult], transcript: List[ChatCompletionMessageParam], stereo_recording_url: str):
        self.test = test
        self.evaluation_results = evaluation_results
        self.transcript = transcript
        self.stereo_recording_url = stereo_recording_url

    def __repr__(self):
        return f"TestResult(test={self.test}, evaluation_results={self.evaluation_results}, transcript={self.transcript}, stereo_recording_url='{self.stereo_recording_url}')"

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

    async def run_tests(self, type: str, phone_number: str) -> List[TestResult]:
        """
        Runs all the tests that were added to the test runner.
        Args:
            type: The type of test to run. Can be TestRunner.INBOUND or TestRunner.OUTBOUND.
            phone_number: The phone number to call (for outbound tests).
        """
        self._start_server()

        # Initialize test status display
        print("\n🔄 Running Tests:\n")
        for i, test in enumerate(self.tests, 1):
            print(f"{i}. {test.scenario.name} ⏳ Pending...")

        async with asyncio.TaskGroup() as tg:
            for i, test in enumerate(self.tests, 1):
                if type == self.INBOUND:
                    tg.create_task(self._run_inbound_test(test, phone_number))
                elif type == self.OUTBOUND:
                    tg.create_task(self._run_outbound_test(test, phone_number))
                    # Move cursor up and update status
                    sys.stdout.write(f"\033[{len(self.tests) - i + 1}A")
                    print(f"{i}. {test.scenario.name} 📞 Calling...", " " * 20)
                    sys.stdout.write(f"\033[{len(self.tests) - i + 1}B")
                else:
                    raise ValueError(f"Invalid test type: {type}. Must be TestRunner.INBOUND or TestRunner.OUTBOUND.")

            evaluated_calls = set()

            while len(evaluated_calls) < len(self.tests):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.ngrok_url}/status") as response:
                        self._status = await response.json()

                # Update status for each test
                for call_id, status in self._status.items():
                    if call_id in self._call_id_to_test:
                        test = self._call_id_to_test[call_id]
                        test_index = self.tests.index(test)
                        status_symbol = "⏳"
                        status_text = "In progress"
                        
                        if status["status"] == "completed":
                            if call_id in self._evaluation_results:
                                status_symbol = "✅"
                                status_text = "Complete"
                            else:
                                status_symbol = "📝"
                                status_text = "Evaluating"
                        
                        # Move cursor up to the test's line
                        sys.stdout.write(f"\033[{len(self.tests) - test_index}A")
                        print(f"{test_index + 1}. {test.scenario.name} ({test.agent.name}) {status_symbol} {status_text}", " " * 20)
                        sys.stdout.write(f"\033[{len(self.tests) - test_index}B")
                        sys.stdout.flush()

                # Check for completed calls to evaluate
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
        print("\n✨ All tests completed!\n")
        
        # Display final results
        print("📊 Test Results:")
        print("=" * 50)
        for call_id, results in self._evaluation_results.items():
            test = self._call_id_to_test[call_id]
            recording_url = self._status[call_id]["stereo_recording_url"]
            print(f"\n🎯 {test.scenario.name} ({test.agent.name})")
            print(f"🔊 Recording URL: {recording_url}")
            for result in results:
                status = "✅" if result.passed else "❌"
                print(f"-- {status} {result.name}: {result.reason}")
        print("\n" + "=" * 50)

        test_results = []
        for call_id, results in self._evaluation_results.items():
            test = self._call_id_to_test[call_id]
            test_results.append(
                TestResult(
                    test=test, 
                    evaluation_results=results,
                    transcript=self._status[call_id]["transcript"] or [], 
                    stereo_recording_url=self._status[call_id]["stereo_recording_url"] or ""
                )
            )
        return test_results

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

        # Start debug monitoring in background
        # asyncio.create_task(self._monitor_server_debug())

    async def _monitor_server_debug(self):
        """
        Continuously monitors and prints server stderr output for debugging.
        """
        assert self.server_process.stderr is not None
        while True:
            line = self.server_process.stderr.readline()
            if line:
                # print(f"🔍 [Server]: {line}", end='', flush=True)
                if "ERROR:" in line:
                    print(f"❌ [Server]: {line}", end='', flush=True)
            if self.server_process.poll() is not None:
                break
            await asyncio.sleep(0.1)

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

    async def _run_outbound_test(self, test: Test, phone_number: str):
        """
        Runs an outbound test.
        Args:
            test: The test to run.
            phone_number: The phone number to call.
        """
        print(f"\nRunning test: {test.scenario.name}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.ngrok_url}/outbound", json={
                    "to": phone_number,
                    "from": self.twilio_phone_number,
                    "scenario_prompt": test.scenario.prompt,
                    "agent_prompt": test.agent.prompt,
                    "agent_voice_id": test.agent.voice_id,
                }) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Server error ({response.status}): {error_text}")
                    
                    response_json = await response.json()
                    print(response_json)
                    self._call_id_to_test[response_json["call_id"]] = test
            except aiohttp.ClientError as e:
                print(f"❌ Failed to make outbound call: {str(e)}")
                raise

    def _run_inbound_test(self, test: Test, phone_number: str):
        """
        Runs an inbound test.
        """
        raise NotImplementedError("Inbound tests are not implemented yet")