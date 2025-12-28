"""
LLM (Large Language Model) integration module.
Handles communication with Mistral model for health assessment.
FIXED VERSION with correct import path
"""

import json
import os
import re
from core.config import settings  # FIXED: Changed from config.settings to core.config

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
                "shared/knowledge_base.json",
                "../shared/knowledge_base.json",
                "../../shared/knowledge_base.json",
                "backend/shared/knowledge_base.json",
                "./shared/knowledge_base.json"
            ]
            
            kb_data = None
            loaded_path = None
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        kb_data = json.load(f)
                        loaded_path = path
                        break
            
            if kb_data and 'symptoms' in kb_data:
                symptoms = kb_data.get("symptoms", [])
                print(f"✅ Loaded {len(symptoms)} symptoms from: {loaded_path}")
                # Print first few symptoms for verification
                print(f"   Sample symptoms: {symptoms[:5]}")
                return symptoms
            else:
                print(f"⚠️  Knowledge base found but no 'symptoms' key")
        except Exception as e:
            print(f"⚠️  Error loading knowledge base: {e}")
        
        # Fallback
        print("⚠️  Using fallback symptom list")
        return ["headache", "fever", "cough", "pain"]
    
    def get_response(self, prompt):
        """Get a response (fallback version)."""
        return "I'm here to help with your health assessment. Please describe your symptoms in detail."
        
    def identify_symptoms(self, text):
        """
        Identify symptoms from patient's free text description.
        """
        text_lower = text.lower()
        matched_symptoms = []
        
        print(f"🔍 Analyzing text: {text_lower}")
        
        # Check each symptom from knowledge base
        for symptom in self.symptoms_list:
            symptom_lower = symptom.lower().strip()
            
            # Simple contains check
            if symptom_lower in text_lower:
                matched_symptoms.append(symptom_lower)
        
        # Remove duplicates
        matched_symptoms = list(set(matched_symptoms))
        
        print(f"🔍 Raw matches: {matched_symptoms}")
        
        # If found symptoms, return them
        if matched_symptoms:
            # Take only the first word
            clean_symptoms = []
            for sym in matched_symptoms:
                main_word = sym.split()[0]
                if main_word not in clean_symptoms:
                    clean_symptoms.append(main_word)
            
            print(f"✅ Final symptoms: {clean_symptoms}")
            return clean_symptoms
        
        print(f"⚠️  No symptoms found")
        return ["general health concern"]
    

    def extract_symptom_details(self, text):
        """
        Extract duration, severity, frequency from free-form text.
        Uses knowledge base keywords for better matching.
        """
        text_lower = text.lower()
        details = {}
        
        # Extract Duration
        duration_patterns = [
            r'(\d+\s*(?:day|days|week|weeks|month|months|year|years|hour|hours))',
            r'(since\s+\w+)',
            r'(for\s+(?:the\s+)?(?:past\s+)?(?:last\s+)?\d+\s+\w+)',
            r'(from\s+\d+\s+\w+)',
            r'(about\s+\d+\s+\w+)'
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Duration"] = match.group(1).strip()
                print(f"✅ Extracted Duration: {details['Duration']}")
                break
        
        # Extract Severity (improved with number detection)
        severity_patterns = [
            r'(\d+)\s*(?:out\s+of|/)\s*10',  # "8/10" or "8 out of 10"
            r'(\d+)/10',
            r'severity\s*:?\s*(\d+)',
            r'pain\s*:?\s*(\d+)',
            r'(severe|mild|moderate|extreme|intense|slight|excruciating|unbearable)'
        ]
        for pattern in severity_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Severity"] = match.group(1).strip()
                print(f"✅ Extracted Severity: {details['Severity']}")
                break
        
        # Extract Frequency (improved)
        frequency_patterns = [
            r'(daily|everyday|every\s+day)',
            r'(every\s+morning|in\s+the\s+morning|morning)',
            r'(every\s+evening|in\s+the\s+evening|evening)',
            r'(every\s+night|at\s+night|night)',
            r'(hourly|every\s+hour)',
            r'(weekly|every\s+week)',
            r'(constantly|always|frequently|occasionally|rarely)',
            r'(\d+\s+times?\s+(?:a|per)\s+\w+)',
            r'(once|twice|thrice)\s+(?:a|per|an)?\s*(\w+)'
        ]
        for pattern in frequency_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Frequency"] = match.group(0).strip()
                print(f"✅ Extracted Frequency: {details['Frequency']}")
                break
        
        # Extract Factors/Triggers
        factor_patterns = [
            r'(?:worse|triggered|caused|worsens|aggravated)\s+(?:by|when|after|with)\s+([^.!?,]+)',
            r'(?:better|improves|relieved)\s+(?:by|when|after|with)\s+([^.!?,]+)'
        ]
        for pattern in factor_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Factors"] = match.group(1).strip()
                print(f"✅ Extracted Factors: {details['Factors']}")
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