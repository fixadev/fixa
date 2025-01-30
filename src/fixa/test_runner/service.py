from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from twilio.rest import Client
import asyncio
import sys
import aiohttp
import uvicorn
from fixa import Test
from fixa.evaluators import BaseEvaluator
from fixa.evaluators.evaluator import EvaluationResponse
from fixa.telemetry.service import ProductTelemetry
from fixa.telemetry.views import RunTestTelemetryEvent, TestResultsTelemetryEvent
from fixa.test_runner.server import CallStatus, app, set_args, set_twilio_client
from fixa.test_runner.views import TestResult

load_dotenv(override=True)
REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "DEEPGRAM_API_KEY", "CARTESIA_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "NGROK_AUTH_TOKEN"]

class TestRunner:
    """
    A TestRunner is responsible for running tests.
    """
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
        self._telemetry = ProductTelemetry()
        self._status: Dict[str, CallStatus] = {}
        self._call_id_to_test: Dict[str, Test] = {}
        self._evaluation_results: Dict[str, EvaluationResponse] = {}

    def add_test(self, test: Test):
        """
        Adds a test to the test runner.
        """
        self.tests.append(test)

    async def run_tests(self, phone_number: str, type: str=OUTBOUND) -> List[TestResult]:
        """
        Runs all the tests that were added to the test runner.
        Args:
            phone_number: The phone number to call (for outbound tests).
            type (optional): The type of test to run. Can be TestRunner.INBOUND or TestRunner.OUTBOUND.
        """
        await self._start_server()

        # Initialize test status display
        print("\n🔄 Running Tests:\n")
        for i, test in enumerate(self.tests, 1):
            print(f"{i}. {test.scenario.name} ⏳ Pending...")
            self._telemetry.capture(RunTestTelemetryEvent(test=test))

        async with asyncio.TaskGroup() as tg, aiohttp.ClientSession() as session:
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

            completed_calls = set()
            all_completed_iterations = 0 # keeps track of how many iterations have been done since all calls were completed

            while len(completed_calls) < len(self.tests):
                async with session.get(f"{self.ngrok_url}/status") as response:
                    self._status = await response.json()

                # Print status with simplified transcript info and recording URL
                for call_id, status in self._status.items():
                    transcript_status = "exists" if status["transcript"] is not None else "None"
                    recording_url = status["stereo_recording_url"] or "None"
                    status_str = status["status"]
                    error = status["error"] or "None"
                    print(f"Call {call_id}: status={status_str}, transcript={transcript_status}, recording={recording_url}, error={error}")

                # Check for completed calls to evaluate
                for call_id, status in self._status.items():
                    if (
                        call_id not in completed_calls
                        and status["status"] != "in_progress"
                    ):
                        if status["status"] == "error":
                            completed_calls.add(call_id)
                        elif (
                            status["status"] == "completed"
                            and status["transcript"] is not None
                            and status["stereo_recording_url"] is not None
                        ):
                            completed_calls.add(call_id)
                            tg.create_task(self._evaluate_call(call_id))

                # Check if all calls are completed
                all_completed = True
                for status in self._status.values():
                    if status["status"] == "in_progress":
                        all_completed = False
                        break
                if all_completed:
                    all_completed_iterations += 1
                    print(f"All calls complete! Waiting for evaluations to finish...{all_completed_iterations} second{all_completed_iterations != 1 and 's' or ''} (60s timeout)")
                else:
                    all_completed_iterations = 0

                # Break if all calls are completed for more than 60 seconds (60 iterations)
                # This catches the case where transcript or stereo_recording_url is never set on a call
                if all_completed_iterations > 60:
                    break

                await asyncio.sleep(1)


        # All tests are complete, stop the server
        await self._stop_server()
        
        print("\n✨ All tests completed!\n")
        
        # Display final results
        print("📊 Test Results:")
        print("=" * 50)
        for call_id, status in self._status.items():
            test = self._call_id_to_test[call_id]
            if status["status"] == "error":
                print(f"\n🎯 {test.scenario.name} ({test.agent.name})")
                print(f"❌ Error: {status['error']}")
            else:
                recording_url = status["stereo_recording_url"]
                print(f"\n🎯 {test.scenario.name} ({test.agent.name})")
                print(f"🔊 Recording URL: {recording_url}")
                if call_id in self._evaluation_results:
                    if 'fixa_observe_call_url' in self._evaluation_results[call_id].extra_data:
                        print(f"🔗 fixa-observe call analysis: {self._evaluation_results[call_id].extra_data['fixa_observe_call_url']}")
                    for result in self._evaluation_results[call_id].evaluation_results:
                        status = "✅" if result.passed else "❌"
                        print(f"-- {status} {result.name}: {result.reason}")
        print("\n" + "=" * 50)

        test_results = []
        for call_id, status in self._status.items():
            test = self._call_id_to_test[call_id]
            if status["status"] == "error":
                test_results.append(
                    TestResult(
                        test=test,
                        evaluation_results=None,
                        transcript=[],
                        stereo_recording_url="",
                        error=status["error"]
                    )
                )
            else:
                test_results.append(
                    TestResult(
                        test=test, 
                        evaluation_results=self._evaluation_results.get(call_id),
                        transcript=status["transcript"] or [], 
                        stereo_recording_url=status["stereo_recording_url"] or "",
                        error=None
                    )
                )
        self._telemetry.capture(TestResultsTelemetryEvent(test_results=test_results))
        return test_results

    async def _evaluate_call(self, call_id: str) -> Optional[EvaluationResponse]:
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

        try:
            print(f"Evaluating call {call_id}...")
            evaluation_results = await self.evaluator.evaluate(test.scenario, call_status["transcript"], call_status["stereo_recording_url"])
            print(f"Evaluated call {call_id}!")
            if evaluation_results is not None:
                self._evaluation_results[call_id] = evaluation_results
                return evaluation_results
        except Exception as e:
            print(f"❌ Failed to evaluate call {call_id}: {str(e)}")

        return None

    async def _start_server(self):
        """
        Starts the server.
        """
        # Initialize the server's global variables
        set_args(self.port, self.ngrok_url)
        set_twilio_client(self._twilio_client)
        
        # Configure uvicorn with shutdown timeout
        config = uvicorn.Config(app, host="0.0.0.0", port=self.port, log_level="info", timeout_keep_alive=5)
        self.server = uvicorn.Server(config)
        
        # Run the server in a background task
        self.server_task = asyncio.create_task(self.server.serve())
        
        # Wait for server to start
        while not self.server.started:
            await asyncio.sleep(0.1)
        
        print("Server started...", flush=True)

    async def _stop_server(self):
        """
        Stops the server gracefully, with a forced exit if needed.
        """
        if hasattr(self, 'server'):
            self.server.should_exit = True
            try:
                # Wait for graceful shutdown with timeout
                await asyncio.wait_for(self.server_task, timeout=5.0)
            except asyncio.TimeoutError:
                print("Server graceful shutdown timed out, forcing exit...")
                self.server.force_exit = True
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass

    async def _run_outbound_test(self, test: Test, phone_number: str):
        """
        Runs an outbound test.
        Args:
            test: The test to run.
            phone_number: The phone number to call.
        """
        # print(f"\nRunning test: {test.scenario.name}")
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
                    self._call_id_to_test[response_json["call_id"]] = test
            except aiohttp.ClientError as e:
                print(f"❌ Failed to make outbound call: {str(e)}")
                raise

    def _run_inbound_test(self, test: Test, phone_number: str):
        """
        Runs an inbound test.
        """
        raise NotImplementedError("Inbound tests are not implemented yet")