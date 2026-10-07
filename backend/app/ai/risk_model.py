from typing import List, Optional


class RiskPriorityModel:
    """
    Risk & Urgency Assessment Model.
    Computes priority level based on symptom severity, duration, and patient parameters.
    """

    @staticmethod
    def evaluate_priority(
        is_emergency: bool,
        symptoms: List[str],
        duration_days: Optional[int] = None,
        age: Optional[int] = None
    ) -> str:
        if is_emergency:
            return "EMERGENCY"

        risk_score = 0

        # Symptom severity scoring
        high_risk_symptoms = ["shortness of breath", "chest discomfort", "dizziness"]
        moderate_risk_symptoms = ["fever", "abdominal pain", "severe headache"]

        for s in symptoms:
            s_lower = s.lower()
            if any(hr in s_lower for hr in high_risk_symptoms):
                risk_score += 3
            elif any(mr in s_lower for mr in moderate_risk_symptoms):
                risk_score += 2
            else:
                risk_score += 1

        # Duration scoring
        if duration_days is not None:
            if duration_days > 14:
                risk_score += 2
            elif duration_days > 7:
                risk_score += 1

        # Age risk factor
        if age is not None:
            if age >= 65 or age <= 2:
                risk_score += 2

        if risk_score >= 5:
            return "HIGH"
        elif risk_score >= 3:
            return "MODERATE"
        else:
            return "LOW"
