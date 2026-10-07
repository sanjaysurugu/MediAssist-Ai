import re
from typing import Dict, List, Optional, Tuple

FORBIDDEN_PHRASES = [
    "you definitely have",
    "you definitely do not have",
    "you don't need a doctor",
    "you do not need a doctor",
    "this medicine will cure you",
    "this drug will cure",
    "you are safe",
    "100% cure",
    "guaranteed diagnosis"
]

MANDATORY_DISCLAIMER = (
    "AI-powered healthcare assistance and educational decision-support platform — not a diagnostic system. "
    "This tool is for educational guidance only and does NOT constitute professional medical advice, diagnosis, "
    "or treatment. Always consult a qualified healthcare provider for medical concerns."
)

EMERGENCY_TRIGGERS = [
    # Chest Pain & Cardiac
    (r"\b(severe|crushing|squeezing)\s+(chest\s+pain|chest\s+pressure|heart\s+pain)\b", "Severe Chest Pain / Possible Cardiac Emergency"),
    (r"\b(chest\s+pain|pressure\s+in\s+chest)\s+(radiating|left\s+arm|jaw|neck)\b", "Chest Pain Radiating to Arm/Jaw"),
    (r"\b(heart\s+attack)\b", "Reported Heart Attack Symptoms"),
    
    # Respiratory Emergency
    (r"\b(can'?t\s+breathe|severe\s+shortness\s+of\s+breath|gasping|suffocating)\b", "Severe Respiratory Distress"),
    (r"\b(anaphylaxis|swollen\s+throat|throat\s+closing|severe\s+allergic\s+reaction)\b", "Suspected Severe Allergic Reaction (Anaphylaxis)"),

    # Neurological / Stroke
    (r"\b(face\s+drooping|arm\s+weakness|slurred\s+speech|stroke)\b", "Suspected Stroke Symptoms (FAST Alert)"),
    (r"\b(loss\s+of\s+consciousness|fainted|passed\s+out|unconscious)\b", "Loss of Consciousness / Syncope"),
    (r"\b(seizure|convulsions|fitting)\b", "Active or Recent Seizure"),

    # Severe Bleeding & Trauma
    (r"\b(uncontrolled\s+bleeding|severe\s+bleeding|gushing\s+blood|coughing\s+up\s+blood)\b", "Severe / Uncontrolled Bleeding"),

    # Suicidal Emergency
    (r"\b(suicide|suicidal|end\s+my\s+life|kill\s+myself|self\s*harm)\b", "Psychiatric Crisis / Suicidal Emergency")
]


class EmergencySafetyLayer:
    """
    Emergency Safety Evaluation Layer.
    Scans user symptom text for high-risk life-threatening medical signals.
    """
    
    @staticmethod
    def check_emergency(text: str) -> Tuple[bool, Optional[str]]:
        normalized_text = text.lower()
        
        for pattern, label in EMERGENCY_TRIGGERS:
            if re.search(pattern, normalized_text):
                return True, label
                
        return False, None


class SafetyValidationGuard:
    """
    Safety Output Validation Layer.
    Ensures generated AI responses do not contain diagnostic or dangerous claims.
    """

    @staticmethod
    def sanitize_text(text: str) -> str:
        sanitized = text
        for phrase in FORBIDDEN_PHRASES:
            # Replace forbidden phrases if detected
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            sanitized = pattern.sub("[consult a physician]", sanitized)
        return sanitized

    @staticmethod
    def get_mandatory_disclaimer() -> str:
        return MANDATORY_DISCLAIMER
