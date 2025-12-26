"""
LLM (Large Language Model) integration module.
Handles communication with Mistral model for health assessment.
Simplified version for web deployment.
"""

import json
import os
from core.config import settings

class LLMManager:
    """Manages LLM operations for health conversations."""
    
    def __init__(self):
        """Initialize LLM manager."""
        self.use_llm = False
        self.llm = None
        self.tokenizer = None
        self.symptoms_list = self._load_symptoms_from_knowledge_base()
        
        # Only initialize LLM if explicitly requested
        if settings.USE_LLM:
            try:
                self._initialize_llm()
            except Exception as e:
                print(f"LLM initialization failed: {e}")
                print("Continuing with fallback mechanisms...")
    
    def _initialize_llm(self):
        """Initialize the Mistral LLM model - simplified for web."""
        if not settings.HUGGING_FACE_TOKEN:
            print("No Hugging Face token provided. Using fallback methods.")
            return
        
        print("Note: Full LLM loading disabled for faster startup.")
        print("Using fallback symptom detection methods.")
        # For production, you would implement proper LLM loading here
        # or use an API-based approach (OpenAI, Anthropic, etc.)
    
    def is_available(self):
        """Check if LLM is available."""
        return self.use_llm
    
    def _load_symptoms_from_knowledge_base(self):
        """Load the comprehensive symptoms list from knowledge_base.json."""
        try:
            # Try multiple paths
            possible_paths = [
                "../shared/knowledge_base.json",
                "../../knowledge_base.json",
                "knowledge_base.json"
            ]
            
            kb_data = None
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        kb_data = json.load(f)
                        break
            
            if kb_data:
                return kb_data.get("symptoms", [])
        except Exception as e:
            print(f"Could not load knowledge base: {e}")
        
        # Fallback symptoms list
        return [
            "headache", "fever", "cough", "fatigue", "pain", "nausea",
            "dizziness", "rash", "vomiting", "diarrhea", "breathing difficulty",
            "confusion", "memory loss", "weakness", "chest pain", "abdominal pain"
        ]
    
    def get_response(self, prompt):
        """Get a response (fallback version)."""
        return "I'm here to help with your health assessment. Please describe your symptoms in detail."
    
    def identify_symptoms(self, text):
        """Identify symptoms from patient's free text description using keyword matching."""
        text_lower = text.lower()
        matched_symptoms = [
            symptom for symptom in self.symptoms_list 
            if symptom.lower() in text_lower
        ]
        return matched_symptoms if matched_symptoms else ["general health concern"]
    
    def generate_questions(self, symptom):
        """Generate follow-up questions about a symptom."""
        return [
            f"How long have you been experiencing {symptom}?",
            f"On a scale of 1-10, how would you rate the severity of your {symptom}?",
            f"How frequently do you experience {symptom}?",
            f"Have you noticed anything that triggers or worsens your {symptom}?"
        ]
    
    def generate_general_questions(self):
        """Generate general health questions."""
        return [
            "Do you have any chronic health conditions?",
            "Are you currently taking any medications?",
            "Have you had any surgeries in the past?",
            "Do you have any allergies?",
            "How would you describe your overall health?"
        ]
    
    def summarize_patient_condition(self, patient_data):
        """Generate a basic summary of patient's condition."""
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        demographic = patient_data.get("demographic", {})
        
        summary = f"Patient {demographic.get('name', 'Unknown')} ({demographic.get('age', 'N/A')} years old) "
        summary += f"presents with {len(symptoms)} reported symptom(s): {', '.join(symptoms)}. "
        summary += "Detailed symptom analysis and general health information have been recorded for clinical review."
        
        return summary
    
    def get_clinical_insights(self, patient_data):
        """Get basic clinical insights."""
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        
        insights = f"Clinical Review Notes:\n"
        insights += f"- Patient presents with {len(symptoms)} symptom(s)\n"
        insights += f"- Symptoms include: {', '.join(symptoms)}\n"
        insights += f"- Recommend thorough examination of each symptom\n"
        insights += f"- Review patient's medical history and current medications\n"
        
        return insights

# Global LLM manager instance
llm_manager = LLMManager()