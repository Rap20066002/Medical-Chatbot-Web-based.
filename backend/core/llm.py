"""
LLM (Large Language Model) integration module.
Handles communication with Mistral-7B model for health assessment.
COMPLETE WORKING VERSION - Properly loads and uses LLM
"""

import json
import os
import re
from core.config import settings

class LLMManager:
    """Manages LLM operations for health conversations."""
    
    def __init__(self):
        """Initialize LLM manager."""
        self.use_llm = False
        self.llm = None
        self.tokenizer = None
        self.symptoms_list = self._load_symptoms_from_knowledge_base()
        
        # Try to initialize LLM if token provided
        if settings.USE_LLM and settings.HUGGING_FACE_TOKEN:
            try:
                print("🔄 Initializing LLM (this may take 2-3 minutes)...")
                self._initialize_llm()
                print("✅ LLM initialized successfully!")
            except Exception as e:
                print(f"⚠️  LLM initialization failed: {e}")
                print("   Falling back to knowledge base system")
        else:
            print("⚠️  LLM disabled (USE_LLM=False or no token)")
            print("   Using fallback knowledge base system")
    
    def _initialize_llm(self):
        """Initialize the Mistral-7B LLM model - OPTIMIZED VERSION"""
        try:
            from ctransformers import AutoModelForCausalLM
            
            print("📥 Loading Mistral-7B model...")
            print("   This will download ~4GB on first run")
            print("   Model: TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
            
            self.llm = AutoModelForCausalLM.from_pretrained(
                "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                model_file="mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                model_type="mistral",
                gpu_layers=0,
                context_length=1024,     # Balanced
                max_new_tokens=256,      # Balanced
                temperature=0.2,         # More focused than 0.3, less rigid than 0.1
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.15,
                threads=4                # Use CPU cores
            )
            
            self.use_llm = True
            print("✅ Mistral-7B loaded successfully!")
            
        except ImportError:
            print("❌ ctransformers not installed")
            print("   Run: pip install ctransformers")
            raise
        except Exception as e:
            print(f"❌ Model loading error: {e}")
            raise
    
    def is_available(self):
        """Check if LLM is available."""
        return self.use_llm
    
    def _load_symptoms_from_knowledge_base(self):
        """Load the comprehensive symptoms list from knowledge_base.json."""
        try:
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
                return symptoms
            else:
                print(f"⚠️  Knowledge base found but no 'symptoms' key")
        except Exception as e:
            print(f"⚠️  Error loading knowledge base: {e}")
        
        # Fallback
        print("⚠️  Using fallback symptom list")
        return ["headache", "fever", "cough", "pain", "nausea", "vomiting", "dizziness"]
    
    def get_response(self, prompt, max_tokens=256):
        """
        Get a response from LLM or fallback.
        
        Args:
            prompt: User's message
            max_tokens: Maximum response length
        
        Returns:
            Generated response text
        """
        if self.use_llm and self.llm:
            try:
                # Format prompt for Mistral Instruct
                formatted_prompt = f"""<s>[INST] You are a helpful medical assistant. Answer the following question briefly and accurately.

Question: {prompt}

Answer: [/INST]"""
                
                response = self.llm(formatted_prompt, max_new_tokens=max_tokens)
                return response.strip()
            
            except Exception as e:
                print(f"LLM generation error: {e}")
                return self._get_fallback_response(prompt)
        else:
            return self._get_fallback_response(prompt)
    
    def _get_fallback_response(self, prompt):
        """Fallback response when LLM unavailable."""
        return "I'm here to help with your health assessment. Please describe your symptoms in detail."
    
    def identify_symptoms(self, text):
        """
        INTELLIGENT symptom identification with context understanding
        """
        text_lower = text.lower()
        
        # Try LLM with medical context
        if self.use_llm and self.llm:
            try:
                prompt = f"""<s>[INST] You are a medical AI. Extract ONLY the main symptoms from this patient description. List them separated by commas, nothing else.

    Patient says: "{text}"

    Symptoms: [/INST]"""
                
                response = self.llm(prompt, max_new_tokens=60)
                
                # Clean up response
                response = response.strip()
                # Remove common LLM artifacts
                response = response.replace("Symptoms:", "").replace("symptoms:", "")
                response = response.replace("The symptoms are:", "")
                response = response.strip()
                
                symptoms = [s.strip().lower() for s in response.split(',')]
                symptoms = [s for s in symptoms if s and 3 <= len(s) <= 40 and not s.startswith("the patient")]
                
                if symptoms:
                    print(f"✅ LLM identified symptoms: {symptoms}")
                    return symptoms[:5]
                
            except Exception as e:
                print(f"⚠️ LLM symptom extraction error: {e}")
        
        # Enhanced keyword matching fallback
        print(f"🔍 Using keyword matching")
        matched_symptoms = []
        
        # Multi-word symptoms first (e.g., "morning headache")
        for symptom in self.symptoms_list:
            symptom_lower = symptom.lower().strip()
            if len(symptom.split()) > 1:  # Multi-word
                if symptom_lower in text_lower:
                    matched_symptoms.append(symptom_lower)
        
        # Then single-word symptoms
        for symptom in self.symptoms_list:
            symptom_lower = symptom.lower().strip()
            if len(symptom.split()) == 1:  # Single word
                # Use word boundaries to avoid false matches
                import re
                if re.search(r'\b' + re.escape(symptom_lower) + r'\b', text_lower):
                    if symptom_lower not in [s.split()[0] for s in matched_symptoms]:
                        matched_symptoms.append(symptom_lower)
        
        if matched_symptoms:
            print(f"✅ Keyword matching found: {matched_symptoms}")
            return matched_symptoms[:5]
        
        return ["general health concern"]
    
    def extract_symptom_details(self, text):
        """
        INTELLIGENT detail extraction with medical understanding
        """
        details = {}
        text_lower = text.lower()
        
        if self.use_llm and self.llm:
            try:
                prompt = f"""<s>[INST] Extract medical information from this patient statement. Format exactly as shown:

    Duration: [how long symptom exists, or "Not mentioned"]
    Severity: [pain scale or descriptor, or "Not mentioned"]
    Frequency: [how often it occurs, or "Not mentioned"]
    Factors: [triggers or what makes it worse, or "Not mentioned"]

    Patient statement: "{text}"

    Extracted information:
    [/INST]"""
                
                response = self.llm(prompt, max_new_tokens=120)
                
                # Parse line by line
                for line in response.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            
                            # Clean up value
                            value = value.replace('[', '').replace(']', '')
                            
                            # Only keep if meaningful
                            if value and value.lower() not in ['not mentioned', 'not specified', 'n/a', 'none', '']:
                                details[key] = value
                
                if details:
                    print(f"✅ LLM extracted: {details}")
                    return details
                
            except Exception as e:
                print(f"⚠️ LLM extraction error: {e}")
        
        # Regex fallback (your existing code is fine, keep it)
        print(f"🔍 Using regex extraction")
        
        # Duration
        duration_patterns = [
            r'(\d+\s*(?:day|days|week|weeks|month|months|year|years))',
            r'(since\s+(?:yesterday|last\s+\w+))',
            r'(for\s+(?:the\s+)?(?:past\s+)?(?:last\s+)?\d+\s+\w+)',
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Duration"] = match.group(1).strip()
                break
        
        # Severity
        severity_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:out\s+of|/)\s*10',
            r'severity\s*:?\s*(\d+)',
            r'(severe|mild|moderate|extreme|intense|terrible|unbearable)',
        ]
        for pattern in severity_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Severity"] = match.group(1).strip()
                break
        
        # Frequency
        frequency_patterns = [
            r'(every\s+(?:day|morning|evening|night|hour))',
            r'(daily|hourly|constantly|frequently)',
            r'(\d+\s+times?\s+(?:a|per)\s+(?:day|week|hour))',
        ]
        for pattern in frequency_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Frequency"] = match.group(0).strip()
                break
        
        # Factors/Triggers
        factor_patterns = [
            r'(?:worse|triggered|worsens?|aggravated)\s+(?:by|when|with|after)\s+([^.,!?]+)',
            r'(?:better|improves?|relieved)\s+(?:by|when|with)\s+([^.,!?]+)',
        ]
        for pattern in factor_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Factors"] = match.group(1).strip()
                break
        
        return details
    
    def generate_questions(self, symptom, existing_details=None):
        """
        INTELLIGENT context-aware question generation
        """
        if existing_details is None:
            existing_details = {}
        
        # Build context about what we know
        known_info = []
        for key, value in existing_details.items():
            if value and value != "Not specified":
                known_info.append(f"{key}: {value}")
        
        known_context = ", ".join(known_info) if known_info else "nothing yet"
        
        if self.use_llm and self.llm:
            try:
                prompt = f"""<s>[INST] You are a medical assistant. Generate 2-3 brief, specific follow-up questions for a patient with {symptom}.

    Already known: {known_context}

    Ask about what's missing (duration, severity, frequency, triggers). Keep questions under 15 words each.

    Questions (one per line):
    [/INST]"""
                
                response = self.llm(prompt, max_new_tokens=120)
                
                questions = []
                for line in response.split('\n'):
                    line = line.strip()
                    # Remove numbering
                    line = re.sub(r'^\d+[\.)]\s*', '', line)
                    # Remove "Question:" prefix
                    line = re.sub(r'^Question:\s*', '', line, flags=re.IGNORECASE)
                    
                    if line and '?' in line and 10 < len(line) < 100:
                        questions.append(line)
                
                if questions:
                    print(f"✅ LLM generated {len(questions)} questions")
                    return questions[:3]
                
            except Exception as e:
                print(f"⚠️ LLM question error: {e}")
        
        # Template fallback
        questions = []
        
        if not existing_details.get("Duration"):
            questions.append(f"How long have you been experiencing {symptom}?")
        
        if not existing_details.get("Severity"):
            questions.append(f"On a scale of 1-10, how severe is your {symptom}?")
        
        if not existing_details.get("Frequency"):
            questions.append(f"How often do you experience {symptom}?")
        
        if not existing_details.get("Factors"):
            questions.append(f"Does anything trigger or worsen your {symptom}?")
        
        return questions[:3]
    
    def summarize_patient_condition(self, patient_data):
        """
        INTELLIGENT clinical summary generation
        """
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        demographic = patient_data.get("demographic", {})
        
        if not symptoms:
            return "Patient presents for general health assessment. No specific symptoms reported at this time."
        
        print(f"🤖 Generating clinical summary for {len(symptoms)} symptom(s)")
        
        if self.use_llm and self.llm:
            try:
                # Build detailed symptom context
                symptom_text = ""
                for sym, details in patient_data.get("per_symptom", {}).items():
                    symptom_text += f"\n- {sym.title()}"
                    if details.get('Duration'):
                        symptom_text += f" (Duration: {details['Duration']}"
                    if details.get('Severity'):
                        symptom_text += f", Severity: {details['Severity']}"
                    if details.get('Frequency'):
                        symptom_text += f", Frequency: {details['Frequency']}"
                    symptom_text += ")"
                
                prompt = f"""<s>[INST] Write a professional 2-3 sentence clinical summary for a medical record.

    Patient: {demographic.get('age', 'Adult')} year old {demographic.get('gender', 'patient')}

    Presenting symptoms:{symptom_text}

    Write a concise clinical summary suitable for a doctor's review:
    [/INST]"""
                
                summary = self.llm(prompt, max_new_tokens=200)
                
                # Clean up
                summary = summary.strip()
                # Remove common artifacts
                summary = re.sub(r'^(Summary:|Clinical Summary:)\s*', '', summary, flags=re.IGNORECASE)
                
                if len(summary) > 30:
                    print(f"✅ LLM summary generated ({len(summary)} chars)")
                    return summary
                
            except Exception as e:
                print(f"⚠️ LLM summary error: {e}")
        
        # Template fallback
        print(f"📝 Using template summary")
        age = demographic.get('age', 'Adult')
        gender = demographic.get('gender', 'patient')
        symptom_list = ', '.join([s.lower() for s in symptoms])
        
        summary = f"{age}-year-old {gender} presents with {len(symptoms)} reported symptom(s): {symptom_list}. "
        
        # Add duration if available
        first_symptom = list(patient_data.get("per_symptom", {}).values())[0]
        if first_symptom.get('Duration'):
            summary += f"Symptoms present for {first_symptom['Duration']}. "
        
        summary += "Detailed symptom analysis and general health information recorded for clinical review."
        
        return summary
    
    def get_clinical_insights(self, patient_data):
        """
        INTELLIGENT clinical insights for doctors
        """
        print(f"🧠 Generating clinical insights...")
        
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        demographic = patient_data.get("demographic", {})
        
        if self.use_llm and self.llm:
            try:
                # Build comprehensive context
                age = demographic.get('age', 'unknown')
                gender = demographic.get('gender', 'unknown')
                
                symptom_details = ""
                for sym, details in patient_data.get("per_symptom", {}).items():
                    symptom_details += f"\n{sym.title()}:"
                    for key, value in details.items():
                        if value and value != "Not specified":
                            symptom_details += f" {key}={value},"
                
                prompt = f"""<s>[INST] Provide brief clinical insights for this patient case:

    Age: {age}, Gender: {gender}
    Symptoms:{symptom_details}

    Provide:
    1. Most likely diagnosis (1-2 conditions)
    2. Key investigations (2-3 tests)
    3. Red flags (1-2 warning signs)

    Keep it under 150 words total.
    [/INST]"""
                
                insights = self.llm(prompt, max_new_tokens=250)
                
                if insights and len(insights) > 50:
                    print(f"✅ Clinical insights generated ({len(insights)} chars)")
                    return insights.strip()
                
            except Exception as e:
                print(f"⚠️ Insights generation error: {e}")
        
        # Template fallback
        print(f"📝 Using template insights")
        return f"""Clinical Review Notes:

    Patient: {demographic.get('age', 'N/A')} year old {demographic.get('gender', 'N/A')}
    Presenting symptoms: {', '.join(symptoms)}

    Recommended Actions:
    - Complete physical examination
    - Review symptom timeline and progression
    - Assess patient's medical history
    - Consider relevant diagnostic tests
    - Monitor for any red flag symptoms

    This case requires thorough evaluation by a qualified healthcare provider."""


# Global LLM manager instance
llm_manager = LLMManager()