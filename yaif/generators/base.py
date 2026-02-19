"""
Base class for YAIF code generators.
"""

from abc import ABC, abstractmethod
from ..models import YAIFInterface, YAIFEnum, YAIFConfig


class BaseGenerator(ABC):
    """All generators implement this interface."""

    @abstractmethod
    def generate(
        self,
        interfaces: list[YAIFInterface],
        enums: list[YAIFEnum],
        config: YAIFConfig,
    ) -> str:
        """Generate code from parsed YAIF definitions."""
        ...