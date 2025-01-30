
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from fixa.test import Test
from fixa.test_runner.views import TestResult

@dataclass
class BaseTelemetryEvent(ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	def properties(self) -> Dict[str, Any]:
		return {k: v for k, v in asdict(self).items() if k != 'name'}

@dataclass
class RunTestTelemetryEvent(BaseTelemetryEvent):
    test: Test
    name: str = 'run_test'

@dataclass
class TestResultsTelemetryEvent(BaseTelemetryEvent):
    test_results: List[TestResult]
    name: str = 'test_results'
