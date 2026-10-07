from abc import ABC, abstractmethod
from app.ai.schemas import SymptomCheckRequest, SymptomCheckResponse


class BaseAIProvider(ABC):
    """
    Abstract Base Class for Modular AI Decision Support Providers.
    Allows swapping Rule Engine, Local NLP Models, or LLM APIs seamlessly.
    """

    @abstractmethod
    def analyze_symptoms(self, request: SymptomCheckRequest) -> SymptomCheckResponse:
        pass
