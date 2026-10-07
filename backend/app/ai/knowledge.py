from typing import List
from app.ai.schemas import MedicalConditionConcern

# Clinical Evidence Mappings Knowledge Base
KNOWLEDGE_BASE = [
    {
        "condition_name": "Upper Respiratory Tract Infection / Viral Flu",
        "keywords": ["fever", "cough", "sore throat", "fatigue"],
        "specialty": "General Medicine",
        "description": "Common viral infection affecting nose, throat, and airways.",
        "educational_summary": (
            "Viral upper respiratory infections typically present with fever, sore throat, and cough. "
            "Hydration and rest are general supportive measures. Consult a general physician if symptoms persist or worsen."
        )
    },
    {
        "condition_name": "Tension Headache or Migraine Pattern",
        "keywords": ["headache", "fatigue", "nausea", "dizziness"],
        "specialty": "Neurology",
        "description": "Neurological headache pattern associated with stress, vascular changes, or eye strain.",
        "educational_summary": (
            "Recurrent or severe headaches may stem from tension, migraines, or dehydration. "
            "A neurologist or general physician can evaluate headache triggers and suggest preventive management."
        )
    },
    {
        "condition_name": "Acute Gastroenteritis / Gastrointestinal Discomfort",
        "keywords": ["nausea", "diarrhea", "abdominal pain", "fever"],
        "specialty": "General Medicine",
        "description": "Inflammation of stomach and intestines caused by viral/bacterial ingestion.",
        "educational_summary": (
            "Gastrointestinal symptoms like nausea or loose stools require monitoring fluid intake to prevent dehydration. "
            "Seek evaluation if severe abdominal pain or high fever develops."
        )
    },
    {
        "condition_name": "Contact Dermatitis or Allergic Skin Reaction",
        "keywords": ["skin rash"],
        "specialty": "Dermatology",
        "description": "Skin inflammation resulting from allergen exposure or local irritation.",
        "educational_summary": (
            "Skin rashes can occur due to allergies, contact irritants, or viral exanthems. "
            "Dermatology evaluation helps identify specific triggers and suitable topical care."
        )
    },
    {
        "condition_name": "Musculoskeletal Strain or Joint Inflammation",
        "keywords": ["joint pain", "back pain"],
        "specialty": "Orthopedics",
        "description": "Injury or inflammation affecting joints, muscles, or ligaments.",
        "educational_summary": (
            "Joint and back discomfort often relate to posture, physical exertion, or local inflammation. "
            "An orthopedist or physical therapist can evaluate joint mechanics and recommend rest or rehab exercises."
        )
    }
]


class KnowledgeRetrievalEngine:
    """
    Medical Knowledge Retrieval Engine.
    Matches extracted symptoms against clinical evidence patterns.
    """

    @staticmethod
    def retrieve_concerns(symptoms: List[str]) -> List[MedicalConditionConcern]:
        symptom_set = {s.lower() for s in symptoms}
        matched_concerns: List[MedicalConditionConcern] = []

        for item in KNOWLEDGE_BASE:
            matches = 0
            for kw in item["keywords"]:
                if any(kw in s for s in symptom_set):
                    matches += 1

            if matches > 0:
                confidence = min(0.4 + (matches * 0.25), 0.95)
                matched_concerns.append(
                    MedicalConditionConcern(
                        condition_name=item["condition_name"],
                        description=item["description"],
                        match_confidence=round(confidence, 2),
                        recommended_specialty=item["specialty"],
                        educational_summary=item["educational_summary"]
                    )
                )

        if not matched_concerns:
            # Fallback general concern if no specific match
            matched_concerns.append(
                MedicalConditionConcern(
                    condition_name="General Non-Specific Symptoms",
                    description="Symptoms require baseline medical clinical correlation.",
                    match_confidence=0.50,
                    recommended_specialty="General Medicine",
                    educational_summary="Consult a primary care physician for a comprehensive physical evaluation."
                )
            )

        # Sort by confidence descending
        matched_concerns.sort(key=lambda x: x.match_confidence, reverse=True)
        return matched_concerns[:3]
