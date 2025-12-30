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
        """Initialize the Mistral-7B LLM model."""
        try:
            from ctransformers import AutoModelForCausalLM
            
            print("📥 Loading Mistral-7B model...")
            print("   This will download ~4GB on first run")
            print("   Model: TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
            
            # Load the GGUF model
            self.llm = AutoModelForCausalLM.from_pretrained(
                "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                model_file="mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                model_type="mistral",
                gpu_layers=0,  # Use CPU (set to 50+ for GPU)
                context_length=2048,
                max_new_tokens=512,
                temperature=0.3,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.1
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
        Identify symptoms from patient's free text description.
        Uses LLM if available, otherwise uses keyword matching.
        
        Args:
            text: Patient's symptom description
        
        Returns:
            List of identified symptoms
        """
        text_lower = text.lower()
        
        # Try LLM first
        if self.use_llm and self.llm:
            try:
                prompt = f"""<s>[INST] You are a medical symptom extraction assistant. Extract only the main symptoms from the following patient description. Return ONLY a comma-separated list of symptoms, nothing else.

Patient description: "{text}"

Symptoms (comma-separated): [/INST]"""
                
                response = self.llm(prompt, max_new_tokens=100)
                
                # Parse LLM response
                symptoms = [s.strip().lower() for s in response.split(',')]
                symptoms = [s for s in symptoms if s and len(s) > 2]
                
                if symptoms:
                    print(f"✅ LLM identified symptoms: {symptoms}")
                    return symptoms[:5]  # Limit to 5 symptoms
                
            except Exception as e:
                print(f"⚠️ LLM symptom extraction error: {e}")
        
        # Fallback to keyword matching
        print(f"🔍 Using keyword matching for: {text_lower}")
        matched_symptoms = []
        
        for symptom in self.symptoms_list:
            symptom_lower = symptom.lower().strip()
            if symptom_lower in text_lower:
                matched_symptoms.append(symptom_lower)
        
        matched_symptoms = list(set(matched_symptoms))
        
        if matched_symptoms:
            clean_symptoms = []
            for sym in matched_symptoms:
                main_word = sym.split()[0]
                if main_word not in clean_symptoms:
                    clean_symptoms.append(main_word)
            
            print(f"✅ Keyword matching found: {clean_symptoms}")
            return clean_symptoms[:5]
        
        print(f"⚠️  No symptoms found, using default")
        return ["general health concern"]
    
    def extract_symptom_details(self, text):
        """
        Extract duration, severity, frequency from free-form text.
        Uses LLM if available, otherwise uses regex patterns.
        
        Args:
            text: Patient's symptom description
        
        Returns:
            Dictionary with Duration, Severity, Frequency, Factors
        """
        details = {}
        text_lower = text.lower()
        
        # Try LLM extraction first
        if self.use_llm and self.llm:
            try:
                prompt = f"""<s>[INST] Extract the following information from the patient's symptom description. Return in this exact format:
Duration: [extracted duration or "Not specified"]
Severity: [extracted severity or "Not specified"]
Frequency: [extracted frequency or "Not specified"]
Factors: [extracted triggers/factors or "Not specified"]

Patient description: "{text}"

Extracted information: [/INST]"""
                
                response = self.llm(prompt, max_new_tokens=150)
                
                # Parse structured response
                for line in response.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if value and value.lower() != "not specified":
                            details[key] = value
                
                if details:
                    print(f"✅ LLM extracted details: {details}")
                    return details
                
            except Exception as e:
                print(f"⚠️ LLM detail extraction error: {e}")
        
        # Fallback to regex extraction
        print(f"🔍 Using regex extraction for details")
        
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
                break
        
        # Extract Severity
        severity_patterns = [
            r'(\d+)\s*(?:out\s+of|/)\s*10',
            r'(\d+)/10',
            r'severity\s*:?\s*(\d+)',
            r'(severe|mild|moderate|extreme|intense)'
        ]
        for pattern in severity_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Severity"] = match.group(1).strip()
                break
        
        # Extract Frequency
        frequency_patterns = [
            r'(daily|everyday|every\s+day)',
            r'(every\s+morning|in\s+the\s+morning)',
            r'(hourly|every\s+hour)',
            r'(constantly|frequently|occasionally)',
            r'(\d+\s+times?\s+(?:a|per)\s+\w+)'
        ]
        for pattern in frequency_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Frequency"] = match.group(0).strip()
                break
        
        # Extract Factors
        factor_patterns = [
            r'(?:worse|triggered|caused|worsens)\s+(?:by|when|after|with)\s+([^.!?,]+)',
            r'(?:better|improves|relieved)\s+(?:by|when|after|with)\s+([^.!?,]+)'
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
        Uses LLM if available for more contextual questions.
        
        Args:
            symptom: Main symptom name
            existing_details: Already extracted information
        
        Returns:
            List of follow-up questions
        """
        if existing_details is None:
            existing_details = {}
        
        # Try LLM question generation
        if self.use_llm and self.llm:
            try:
                known_info = ", ".join([f"{k}: {v}" for k, v in existing_details.items()])
                
                prompt = f"""<s>[INST] Generate 2-3 specific medical follow-up questions for a patient experiencing {symptom}. 

Already known: {known_info if known_info else "Nothing yet"}

Generate questions to learn about:
- Duration (if not known)
- Severity (if not known)
- Frequency (if not known)
- Triggers or aggravating factors (if not known)

Return only the questions, one per line, numbered 1., 2., 3.

Questions: [/INST]"""
                
                response = self.llm(prompt, max_new_tokens=200)
                
                # Parse questions
                questions = []
                for line in response.split('\n'):
                    line = line.strip()
                    # Remove numbering
                    line = re.sub(r'^\d+\.\s*', '', line)
                    if line and '?' in line:
                        questions.append(line)
                
                if questions:
                    print(f"✅ LLM generated {len(questions)} questions")
                    return questions[:3]
                
            except Exception as e:
                print(f"⚠️ LLM question generation error: {e}")
        
        # Fallback to template questions
        questions = []
        
        if not existing_details.get("Duration"):
            questions.append(f"How long have you been experiencing {symptom}?")
        
        if not existing_details.get("Severity"):
            questions.append(f"On a scale of 1-10, how would you rate the severity of your {symptom}?")
        
        if not existing_details.get("Frequency"):
            questions.append(f"How frequently do you experience {symptom}?")
        
        if not existing_details.get("Factors"):
            questions.append(f"Have you noticed anything that triggers or worsens your {symptom}?")
        
        return questions
    
    def summarize_patient_condition(self, patient_data):
        """
        Generate a clinical summary of patient's condition.
        Uses LLM if available for more insightful summaries.
        
        Args:
            patient_data: Complete patient information
        
        Returns:
            Clinical summary text
        """
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        demographic = patient_data.get("demographic", {})
        
        print(f"🤖 Generating summary for {len(symptoms)} symptom(s)")
        
        # Try LLM summarization
        if self.use_llm and self.llm:
            try:
                # Build context
                symptom_details = ""
                for sym, details in patient_data.get("per_symptom", {}).items():
                    symptom_details += f"\n- {sym}: "
                    symptom_details += f"Duration: {details.get('Duration', 'unknown')}, "
                    symptom_details += f"Severity: {details.get('Severity', 'unknown')}, "
                    symptom_details += f"Frequency: {details.get('Frequency', 'unknown')}"
                
                prompt = f"""<s>[INST] Write a brief clinical summary (2-3 sentences) for the following patient case:

Patient: {demographic.get('age', 'Unknown')} year old {demographic.get('gender', 'patient')}

Presenting symptoms:
{symptom_details}

Write a professional clinical summary suitable for a doctor's review: [/INST]"""
                
                summary = self.llm(prompt, max_new_tokens=200)
                
                if summary and len(summary) > 20:
                    print(f"✅ LLM generated clinical summary ({len(summary)} chars)")
                    return summary.strip()
                
            except Exception as e:
                print(f"⚠️ LLM summarization error: {e}")
        
        # Fallback to template summary
        print(f"📝 Using template summary")
        summary = f"Patient {demographic.get('name', 'Unknown')} ({demographic.get('age', 'N/A')} years old) "
        summary += f"presents with {len(symptoms)} reported symptom(s): {', '.join(symptoms)}. "
        summary += "Detailed symptom analysis and general health information have been recorded for clinical review."
        
        return summary
    
    def get_clinical_insights(self, patient_data):
        """
        Get AI-powered clinical insights.
        Only available when LLM is loaded.
        
        Args:
            patient_data: Complete patient information
        
        Returns:
            Clinical insights text
        """
        print(f"🧠 Generating clinical insights...")
        
        if self.use_llm and self.llm:
            try:
                symptoms = list(patient_data.get("per_symptom", {}).keys())
                
                # Build detailed context
                context = f"Patient age: {patient_data.get('demographic', {}).get('age', 'unknown')}\n"
                context += f"Gender: {patient_data.get('demographic', {}).get('gender', 'unknown')}\n\n"
                context += "Symptoms:\n"
                
                for sym, details in patient_data.get("per_symptom", {}).items():
                    context += f"- {sym}:\n"
                    context += f"  Duration: {details.get('Duration', 'not specified')}\n"
                    context += f"  Severity: {details.get('Severity', 'not specified')}\n"
                    context += f"  Frequency: {details.get('Frequency', 'not specified')}\n"
                
                prompt = f"""<s>[INST] As a medical AI assistant, provide clinical insights for this case:

{context}

Provide:
1. Possible differential diagnoses (3-4 most likely)
2. Recommended investigations
3. Red flags to watch for
4. General advice

Keep it brief and professional: [/INST]"""
                
                insights = self.llm(prompt, max_new_tokens=400)
                
                if insights:
                    print(f"✅ LLM generated clinical insights ({len(insights)} chars)")
                    return insights.strip()
                
            except Exception as e:
                print(f"⚠️ LLM insights error: {e}")
        
        # Fallback
        print(f"📝 Using template insights")
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        insights = f"Clinical Review Notes:\n"
        insights += f"- Patient presents with {len(symptoms)} symptom(s)\n"
        insights += f"- Symptoms include: {', '.join(symptoms)}\n"
        insights += f"- Recommend thorough examination of each symptom\n"
        insights += f"- Review patient's medical history and current medications\n"
        
        return insights


# Global LLM manager instance
llm_manager = LLMManager()