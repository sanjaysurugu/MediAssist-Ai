from app.ai.extractor import SymptomExtractor
from app.ai.knowledge import KnowledgeRetrievalEngine
from app.ai.providers.base import BaseAIProvider
from app.ai.risk_model import RiskPriorityModel
from app.ai.safety import EmergencySafetyLayer, SafetyValidationGuard
from app.ai.schemas import SymptomCheckRequest, SymptomCheckResponse


class RuleBasedAIProvider(BaseAIProvider):
    """
    Built-in Offline Clinical Rule Engine Provider.
    Executes multi-layer safety check, symptom extraction, evidence retrieval, and risk scoring.
    """

    def analyze_symptoms(self, request: SymptomCheckRequest) -> SymptomCheckResponse:
        # 1. Emergency Safety Layer Scan
        is_emergency, emergency_trigger = EmergencySafetyLayer.check_emergency(request.symptoms)

        if is_emergency:
            # Immediate Emergency Bypass
            return SymptomCheckResponse(
                is_emergency=True,
                priority_level="EMERGENCY",
                summary=f"🚨 EMERGENCY ALERT DETECTED: [{emergency_trigger}]",
                detected_symptoms=["Emergency Indicator Detected"],
                possible_areas_of_concern=[],
                recommended_next_steps=[
                    "CALL EMERGENCY SERVICES IMMEDIATELY (e.g. 911 / 112 / 102).",
                    "Do not attempt to drive yourself; seek urgent immediate transport.",
                    "Notify someone nearby of your emergency state immediately."
                ],
                suggested_department="Emergency Room / Urgent Care",
                urgency_recommendation="CRITICAL EMERGENCY: Seek immediate emergency medical care.",
                disclaimer=SafetyValidationGuard.get_mandatory_disclaimer()
            )

        # 2. Symptom Extraction
        detected_symptoms = SymptomExtractor.extract_symptoms(request.symptoms)

        # 3. Medical Knowledge Retrieval
        possible_concerns = KnowledgeRetrievalEngine.retrieve_concerns(detected_symptoms)

        # 4. Risk & Urgency Model
        priority = RiskPriorityModel.evaluate_priority(
            is_emergency=False,
            symptoms=detected_symptoms,
            duration_days=request.duration_days,
            age=request.age
        )

        # Determine Recommended Department from top concern
        top_department = possible_concerns[0].recommended_specialty if possible_concerns else "General Medicine"

        # Construct Next Steps & Urgency Recommendation
        if priority == "HIGH":
            urgency_msg = "Consult a physician within 24 hours for evaluation."
            next_steps = [
                "Schedule a consultation with a doctor promptly.",
                "Monitor for worsening symptoms such as high fever or shortness of breath.",
                "Keep a log of symptom onset, intensity, and triggers."
            ]
        elif priority == "MODERATE":
            urgency_msg = "Schedule a routine consultation with a doctor if symptoms persist."
            next_steps = [
                "Book an appointment with a healthcare professional.",
                "Maintain adequate hydration, rest, and nutrition.",
                "Avoid unprescribed medications without professional advice."
            ]
        else:
            urgency_msg = "Monitor symptoms and practice general self-care."
            next_steps = [
                "Rest and maintain good hydration.",
                "If symptoms worsen or do not improve after 3-5 days, consult a physician."
            ]

        # 5. Safety Validation Guard (sanitize output text)
        sanitized_summary = SafetyValidationGuard.sanitize_text(
            f"Based on your report of '{request.symptoms[:60]}...', we identified key symptoms and educational guidance."
        )

        return SymptomCheckResponse(
            is_emergency=False,
            priority_level=priority,
            summary=sanitized_summary,
            detected_symptoms=detected_symptoms,
            possible_areas_of_concern=possible_concerns,
            recommended_next_steps=next_steps,
            suggested_department=top_department,
            urgency_recommendation=urgency_msg,
            disclaimer=SafetyValidationGuard.get_mandatory_disclaimer()
        )
