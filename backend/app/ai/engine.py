from app.ai.providers.base import BaseAIProvider
from app.ai.providers.rule_provider import RuleBasedAIProvider
from app.ai.schemas import SymptomCheckRequest, SymptomCheckResponse


class AIAssistantEngine:
    """
    Central AI Multi-Layer Assistant Engine.
    Instantiates modular provider and orchestrates symptom analysis.
    """

    def __init__(self, provider: BaseAIProvider = None):
        # Default to RuleBasedAIProvider for offline, deterministic reliability
        self.provider = provider or RuleBasedAIProvider()

    def process_symptoms(self, request: SymptomCheckRequest) -> SymptomCheckResponse:
        return self.provider.analyze_symptoms(request)


# Singleton AI Engine instance for application reuse
ai_engine = AIAssistantEngine()
