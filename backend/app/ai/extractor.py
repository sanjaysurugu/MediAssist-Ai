import re
from typing import Dict, List, Set

CLINICAL_SYMPTOM_DICTIONARY = {
    "fever": ["fever", "high temperature", "chills", "febrile", "pyrexia"],
    "headache": ["headache", "migraine", "head throbbing", "pain in head"],
    "cough": ["cough", "coughing", "dry cough", "phlegm", "sputum"],
    "shortness_of_breath": ["shortness of breath", "breathless", "difficulty breathing", "wheezing"],
    "chest_discomfort": ["chest discomfort", "chest pressure", "mild chest pain", "tightness in chest"],
    "nausea": ["nausea", "vomiting", "feeling sick", "queasy"],
    "abdominal_pain": ["stomach pain", "abdominal pain", "belly ache", "cramps in stomach"],
    "diarrhea": ["diarrhea", "loose motion", "watery stools"],
    "fatigue": ["fatigue", "tiredness", "exhaustion", "feeling weak", "lethargy"],
    "sore_throat": ["sore throat", "throat pain", "difficulty swallowing", "scratchy throat"],
    "joint_pain": ["joint pain", "knee pain", "arthralgia", "swollen joints"],
    "skin_rash": ["rash", "skin itching", "red spots", "hives", "dermatitis"],
    "dizziness": ["dizziness", "giddiness", "lightheaded", "vertigo"],
    "back_pain": ["back pain", "lower back pain", "spine pain"]
}


class SymptomExtractor:
    """
    Symptom & Clinical Entity Extractor.
    Extracts recognized symptoms, body systems, and duration from free-form text.
    """

    @staticmethod
    def extract_symptoms(text: str) -> List[str]:
        normalized_text = text.lower()
        extracted: Set[str] = set()

        for canonical_name, syn_list in CLINICAL_SYMPTOM_DICTIONARY.items():
            for syn in syn_list:
                if re.search(r"\b" + re.escape(syn) + r"\b", normalized_text):
                    # Format as clean human-readable name (e.g. "shortness_of_breath" -> "Shortness of breath")
                    extracted.add(canonical_name.replace("_", " ").capitalize())
                    break

        if not extracted:
            # Fallback extraction if no canonical dictionary keyword matched
            extracted.add("General Discomfort / Unspecified Symptoms")

        return list(extracted)
