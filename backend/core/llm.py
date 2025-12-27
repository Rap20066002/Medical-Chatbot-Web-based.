"""
LLM (Large Language Model) integration module.
Handles communication with Mistral model for health assessment.
FIXED VERSION with proper fallback mechanisms
"""

import json
import os
import re
from config.settings import settings

class LLMManager:
    """Manages LLM operations for health conversations."""
    
    def __init__(self):
        """Initialize LLM manager."""
        self.use_llm = False
        self.llm = None
        self.tokenizer = None
        self.symptoms_list = self._load_symptoms_from_knowledge_base()
        
        # Only try to initialize LLM if explicitly enabled
        if settings.USE_LLM:
            try:
                self._initialize_llm()
            except Exception as e:
                print(f"⚠️  LLM initialization failed: {e}")
                print("   Using fallback knowledge base system")
    
    def _initialize_llm(self):
        """Initialize the Mistral LLM model - simplified for web."""
        if not settings.HUGGING_FACE_TOKEN:
            print("No Hugging Face token provided. Using fallback methods.")
            return
        
        print("Note: Full LLM loading disabled for faster startup.")
        print("Using fallback symptom detection methods.")
        # For production, you would implement proper LLM loading here
    
    def is_available(self):
        """Check if LLM is available."""
        return self.use_llm
    
    def _load_symptoms_from_knowledge_base(self):
        """Load the comprehensive symptoms list from knowledge_base.json."""
        try:
            # Try multiple paths
            possible_paths = [
                "knowledge_base.json",
                "../knowledge_base.json",
                "../../knowledge_base.json",
                "../shared/knowledge_base.json"
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
        """
        Identify symptoms from patient's free text description using keyword matching.
        Case-insensitive matching from knowledge base.
        """
        text_lower = text.lower()
        matched_symptoms = []
        
        for symptom in self.symptoms_list:
            if symptom.lower() in text_lower:
                matched_symptoms.append(symptom)
        
        # Remove duplicates while preserving order
        matched_symptoms = list(dict.fromkeys(matched_symptoms))
        
        return matched_symptoms if matched_symptoms else ["general health concern"]
    
    def extract_symptom_details(self, text):
        """
        Extract duration, severity, frequency from free-form text.
        Returns dict with extracted information.
        """
        text_lower = text.lower()
        details = {}
        
        # Extract Duration
        duration_patterns = [
            r'(\d+\s*(?:day|days|week|weeks|month|months|year|years|hour|hours))',
            r'(since\s+\w+)',
            r'(for\s+(?:the\s+)?(?:past\s+)?(?:last\s+)?\d+\s+\w+)',
            r'(about\s+\d+\s+\w+)'
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Duration"] = match.group(1).strip()
                break
        
        # Extract Severity
        severity_patterns = [
            r'severity\s*:?\s*(\d+)',
            r'(\d+)\s*(?:out of|/)\s*10',
            r'(severe|mild|moderate|extreme|intense|slight)',
            r'(very\s+\w+)',
            r'severity\s+(?:of\s+)?(\d+)'
        ]
        for pattern in severity_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Severity"] = match.group(1).strip()
                break
        
        # Extract Frequency
        frequency_patterns = [
            r'((?:every|each)\s+\w+)',
            r'((?:once|twice|thrice)\s+(?:a|per|an)?\s*\w+)',
            r'(\d+\s+times?\s+(?:a|per)\s+\w+)',
            r'(constantly|always|frequently|occasionally|rarely|daily|weekly|hourly)',
            r'(all\s+day|throughout\s+the\s+day)'
        ]
        for pattern in frequency_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Frequency"] = match.group(1).strip()
                break
        
        # Extract Factors/Triggers
        factor_patterns = [
            r'(?:worse|triggered|caused|worsens|aggravated)\s+(?:by|when|after)\s+([^.!?]+)',
            r'(?:better|improves|relieved)\s+(?:by|when|after)\s+([^.!?]+)'
        ]
        for pattern in factor_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Factors"] = match.group(1).strip()
                break
        
        return details
    
    def generate_questions(self, symptom, existing_details=None):
        """
        Generate follow-up questions about a symptom.
        Skip questions if info already provided.
        """
        if existing_details is None:
            existing_details = {}
        
        questions = []
        
        # Only ask if not already answered
        if not existing_details.get("Duration"):
            questions.append(f"How long have you been experiencing {symptom}?")
        
        if not existing_details.get("Severity"):
            questions.append(f"On a scale of 1-10, how would you rate the severity of your {symptom}?")
        
        if not existing_details.get("Frequency"):
            questions.append(f"How frequently do you experience {symptom}?")
        
        if not existing_details.get("Factors"):
            questions.append(f"Have you noticed anything that triggers or worsens your {symptom}?")
        
        return questions
    
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
        try:
            symptoms = list(patient_data.get("per_symptom", {}).keys())
            demographic = patient_data.get("demographic", {})
            
            summary = f"Patient {demographic.get('name', 'Unknown')} ({demographic.get('age', 'N/A')} years old) "
            summary += f"presents with {len(symptoms)} reported symptom(s): {', '.join(symptoms)}. "
            summary += "Detailed symptom analysis and general health information have been recorded for clinical review."
            
            return summary
        except Exception as e:
            return "Health assessment completed. Please review detailed information below."
    
    def get_clinical_insights(self, patient_data):
        """Get basic clinical insights."""
        try:
            symptoms = list(patient_data.get("per_symptom", {}).keys())
            
            insights = f"Clinical Review Notes:\n"
            insights += f"- Patient presents with {len(symptoms)} symptom(s)\n"
            insights += f"- Symptoms include: {', '.join(symptoms)}\n"
            insights += f"- Recommend thorough examination of each symptom\n"
            insights += f"- Review patient's medical history and current medications\n"
            
            return insights
        except Exception as e:
            return "Clinical insights unavailable. Please review patient data manually."

# Global LLM manager instance
llm_manager = LLMManager()