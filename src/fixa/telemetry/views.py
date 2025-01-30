
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Dict

from fixa.test import Test

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
