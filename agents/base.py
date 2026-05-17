from abc import ABC, abstractmethod
from typing import Any, Dict, List
import logging

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.reasoning_steps: List[str] = []
        
        # Basic logger setup
        self.logger = logging.getLogger(self.name)
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            self.logger.setLevel(logging.INFO)

    def log_reasoning(self, step: str) -> None:
        """Log a reasoning step to the internal list and via standard logger."""
        self.reasoning_steps.append(step)
        self.logger.info(step)

    def clear_reasoning(self) -> None:
        """Clear previous reasoning steps."""
        self.reasoning_steps = []

    @abstractmethod
    async def process(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Process the input and return structured JSON output.
        Must include reasoning_steps in the output.
        """
        pass
