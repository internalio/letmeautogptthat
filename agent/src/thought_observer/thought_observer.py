from abc import ABC, abstractmethod


class ThoughtObserver(ABC):
    """Observes thoughts made by an Agent. Can be used to record, print, etc."""

    @abstractmethod
    def __call__(self, thought: str, raw_data: str):
        """Handle new incoming thought"""
