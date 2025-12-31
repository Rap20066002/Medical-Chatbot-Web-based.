"""
LLM Module - FIXED TOKEN LIMIT ISSUE
Increases context window and adds prompt truncation
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
        """Initialize the Mistral-7B LLM model with INCREASED context window"""
        try:
            from ctransformers import AutoModelForCausalLM
            
            print("📥 Loading Mistral-7B model...")
            
            self.llm = AutoModelForCausalLM.from_pretrained(
                "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                model_file="mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                model_type="mistral",
                gpu_layers=0,
                context_length=4096,  # 🔧 INCREASED from 1024 to 4096
                max_new_tokens=512,   # 🔧 INCREASED from 256 to 512
                temperature=0.2,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.15,
                threads=4
            )
            
            self.use_llm = True
            print("✅ Mistral-7B loaded with 4096 token context!")
            
        except Exception as e:
            print(f"❌ Model loading error: {e}")
            raise
    
    def is_available(self):
        """Check if LLM is available."""
        return self.use_llm
    
    def _load_symptoms_from_knowledge_base(self):
        """Load symptoms list from knowledge_base.json"""
        try:
            possible_paths = [
                "shared/knowledge_base.json",
                "../shared/knowledge_base.json",
                "../../shared/knowledge_base.json",
                "backend/shared/knowledge_base.json",
                "./shared/knowledge_base.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        kb_data = json.load(f)
                        symptoms = kb_data.get("symptoms", [])
                        print(f"✅ Loaded {len(symptoms)} symptoms from: {path}")
                        return symptoms
        except Exception as e:
            print(f"⚠️  Error loading knowledge base: {e}")
        
        print("⚠️  Using fallback symptom list")
        return ["headache", "fever", "cough", "pain", "nausea", "vomiting", "dizziness"]
    
    def _truncate_text(self, text, max_chars=2000):
        """
        🔧 NEW HELPER: Truncate text to prevent token overflow
        Rough estimate: 1 token ≈ 4 characters
        """
        if len(text) <= max_chars:
            return text
        
        return text[:max_chars] + "... [truncated for length]"
    
    def _summarize_patient_data(self, patient_data):
        """
        🔧 NEW HELPER: Create concise summary of patient data
        Reduces token count for prompts
        """
        summary_parts = []
        
        # Demographics (keep concise)
        demo = patient_data.get("demographic", {})
        age = demo.get('age', 'unknown')
        gender = demo.get('gender', 'unknown')
        summary_parts.append(f"Patient: {age}yo {gender}")
        
        # Symptoms (limit to top 5)
        symptoms = list(patient_data.get("per_symptom", {}).keys())[:5]
        if symptoms:
            summary_parts.append(f"Symptoms: {', '.join(symptoms)}")
        
        # Key details from first symptom only
        if patient_data.get("per_symptom"):
            first_symptom = list(patient_data["per_symptom"].values())[0]
            details = []
            if first_symptom.get("Duration"):
                details.append(f"Duration: {first_symptom['Duration']}")
            if first_symptom.get("Severity"):
                details.append(f"Severity: {first_symptom['Severity']}")
            if details:
                summary_parts.append(" | ".join(details))
        
        return " | ".join(summary_parts)
    
    def identify_symptoms(self, text):
        """Identify symptoms with truncation"""
        text_lower = text.lower()
        
        # Truncate input if too long
        text_truncated = self._truncate_text(text, max_chars=1500)
        
        if self.use_llm and self.llm:
            try:
                prompt = f"""<s>[INST] Extract ONLY medical symptoms from this text (not severity/time):

Text: "{text_truncated}"

List symptoms comma-separated:
[/INST]"""
                
                response = self.llm(prompt, max_new_tokens=60)
                
                response = response.strip().lower()
                response = response.replace("symptoms:", "").replace("medical symptoms:", "").strip()
                
                symptoms = [s.strip() for s in response.split(',')]
                
                # Filter valid symptoms
                filtered = []
                invalid_words = [
                    'severe', 'mild', 'daily', 'weekly', 'every', 'morning',
                    'day', 'week', 'constant', 'frequent', '/10'
                ]
                
                for symptom in symptoms:
                    symptom = symptom.strip()
                    if any(inv in symptom for inv in invalid_words):
                        continue
                    if len(symptom) < 3 or len(symptom) > 40:
                        continue
                    if not any(c.isalpha() for c in symptom):
                        continue
                    filtered.append(symptom)
                
                if filtered:
                    print(f"✅ LLM identified: {filtered[:5]}")
                    return filtered[:5]
                
            except Exception as e:
                print(f"⚠️ LLM symptom extraction error: {e}")
        
        # Fallback: keyword matching
        matched_symptoms = []
        for symptom in self.symptoms_list:
            symptom_lower = symptom.lower().strip()
            if re.search(r'\b' + re.escape(symptom_lower) + r'\b', text_lower):
                if symptom_lower not in matched_symptoms:
                    matched_symptoms.append(symptom_lower)
        
        if matched_symptoms:
            return matched_symptoms[:5]
        
        return ["general health concern"]
    
    def extract_symptom_details(self, text):
        """Extract details with truncation"""
        details = {}
        text_lower = text.lower()
        
        # Truncate input
        text_truncated = self._truncate_text(text, max_chars=1500)
        
        if self.use_llm and self.llm:
            try:
                prompt = f"""<s>[INST] Extract temporal/severity info ONLY:

Text: "{text_truncated}"

Format:
Duration: [e.g. "3 days" or "Not mentioned"]
Severity: [e.g. "8/10" or "Not mentioned"]
Frequency: [e.g. "daily" or "Not mentioned"]
Factors: [triggers or "Not mentioned"]
[/INST]"""
                
                response = self.llm(prompt, max_new_tokens=120)
                
                for line in response.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip().replace('[', '').replace(']', '')
                            
                            if value and value.lower() not in ['not mentioned', 'not specified', 'n/a']:
                                details[key] = value
                
                if details:
                    print(f"✅ LLM extracted: {details}")
                    return details
                
            except Exception as e:
                print(f"⚠️ LLM extraction error: {e}")
        
        # Regex fallback (unchanged)
        duration_patterns = [
            r'for\s+(?:the\s+)?(?:past\s+)?(?:last\s+)?(\d+\s+(?:day|days|week|weeks|month|months))',
            r'(\d+\s+(?:day|days|week|weeks))\s+(?:now|ago)',
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Duration"] = match.group(1).strip()
                break
        
        severity_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:out\s+of|/)\s*10',
            r'\b(severe|mild|moderate|extreme|intense)\b',
        ]
        for pattern in severity_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Severity"] = match.group(1).strip()
                break
        
        frequency_patterns = [
            r'(every\s+(?:day|morning|evening|night|hour))',
            r'(daily|hourly|constantly|frequently)',
        ]
        for pattern in frequency_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Frequency"] = match.group(1).strip()
                break
        
        return details
    
    def generate_questions(self, symptom, existing_details=None):
        """Generate questions with context"""
        if existing_details is None:
            existing_details = {}
        
        known_info = []
        for key, value in existing_details.items():
            if value and value != "Not specified":
                known_info.append(f"{key}: {value}")
        
        known_context = ", ".join(known_info) if known_info else "nothing"
        
        if self.use_llm and self.llm:
            try:
                prompt = f"""<s>[INST] Patient has: {symptom}
Known: {known_context}

Generate 2-3 brief questions (under 15 words each) for missing info:
[/INST]"""
                
                response = self.llm(prompt, max_new_tokens=120)
                
                questions = []
                for line in response.split('\n'):
                    line = line.strip()
                    line = re.sub(r'^\d+[\.)]\s*', '', line)
                    line = re.sub(r'^[-•]\s*', '', line)
                    
                    if line and '?' in line and 10 < len(line) < 100:
                        questions.append(line)
                
                if questions:
                    print(f"✅ Generated {len(questions)} questions")
                    return questions[:3]
                
            except Exception as e:
                print(f"⚠️ Question generation error: {e}")
        
        # Template fallback
        questions = []
        if not existing_details.get("Duration"):
            questions.append(f"How long have you had {symptom}?")
        if not existing_details.get("Severity"):
            questions.append(f"How severe is your {symptom} (1-10)?")
        if not existing_details.get("Frequency"):
            questions.append(f"How often do you experience {symptom}?")
        
        return questions[:3]
    
    def summarize_patient_condition(self, patient_data):
        """
        🔧 FIXED: Generate summary with CONCISE input
        """
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        demographic = patient_data.get("demographic", {})
        
        if not symptoms:
            return "Patient presents for general health assessment."
        
        print(f"🤖 Generating summary for {len(symptoms)} symptom(s)")
        
        if self.use_llm and self.llm:
            try:
                # 🔧 Use concise patient summary
                patient_summary = self._summarize_patient_data(patient_data)
                
                prompt = f"""<s>[INST] Write a 2-3 sentence clinical summary:

{patient_summary}

Summary:
[/INST]"""
                
                print(f"📊 Prompt length: {len(prompt)} chars")
                
                summary = self.llm(prompt, max_new_tokens=200)
                summary = summary.strip()
                summary = re.sub(r'^(Summary:|Clinical Summary:)\s*', '', summary, flags=re.IGNORECASE)
                
                if len(summary) > 30:
                    print(f"✅ Summary generated ({len(summary)} chars)")
                    return summary
                
            except Exception as e:
                print(f"⚠️ Summary generation error: {e}")
        
        # Template fallback
        age = demographic.get('age', 'Adult')
        gender = demographic.get('gender', 'patient')
        symptom_list = ', '.join([s.lower() for s in symptoms[:3]])  # Limit to 3
        
        summary = f"{age}yo {gender} with {len(symptoms)} symptom(s): {symptom_list}."
        
        first_symptom = list(patient_data.get("per_symptom", {}).values())[0]
        if first_symptom.get('Duration'):
            summary += f" Duration: {first_symptom['Duration']}."
        
        return summary
    
    def get_clinical_insights(self, patient_data):
        """
        🔧 FIXED: Generate insights with CONCISE input to avoid token overflow
        """
        print(f"🧠 Generating clinical insights...")
        
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        demographic = patient_data.get("demographic", {})
        
        if self.use_llm and self.llm:
            try:
                # 🔧 Create VERY concise summary
                age = demographic.get('age', 'unknown')
                gender = demographic.get('gender', 'unknown')
                
                # Limit symptoms to top 3
                symptom_list = ", ".join(symptoms[:3])
                
                # Get only key details from first symptom
                key_details = ""
                if patient_data.get("per_symptom"):
                    first = list(patient_data["per_symptom"].values())[0]
                    details = []
                    if first.get("Duration"):
                        details.append(f"Duration: {first['Duration']}")
                    if first.get("Severity"):
                        details.append(f"Severity: {first['Severity']}")
                    key_details = " | ".join(details)
                
                # 🔧 VERY SHORT PROMPT to stay under token limit
                prompt = f"""<s>[INST] Clinical insights for:

Patient: {age}yo {gender}
Symptoms: {symptom_list}
{key_details}

Provide brief:
1. Top 2 differential diagnoses
2. Key investigations (2-3 tests)
3. Red flags (1-2 warnings)

Keep under 150 words total:
[/INST]"""
                
                print(f"📊 Prompt length: {len(prompt)} chars (~{len(prompt)//4} tokens)")
                
                insights = self.llm(prompt, max_new_tokens=300)
                
                if insights and len(insights) > 50:
                    print(f"✅ Insights generated ({len(insights)} chars)")
                    return insights.strip()
                
            except Exception as e:
                print(f"⚠️ Insights generation error: {e}")
                import traceback
                print(traceback.format_exc())
        
        # Template fallback
        return f"""Clinical Review Notes:

Patient: {demographic.get('age', 'N/A')}yo {demographic.get('gender', 'N/A')}
Presenting symptoms: {', '.join(symptoms[:3])}

Recommended Actions:
- Complete physical examination
- Review symptom progression
- Consider relevant diagnostic tests
- Monitor for red flag symptoms

Requires thorough evaluation by healthcare provider."""


# Global LLM manager instance
llm_manager = LLMManager()