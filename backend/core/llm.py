"""
LLM Module - COMPLETELY FIXED VERSION
Fixes symptom extraction, detail mapping, and question generation
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
        """Initialize the Mistral-7B LLM model"""
        try:
            from ctransformers import AutoModelForCausalLM
            
            print("📥 Loading Mistral-7B model...")
            
            self.llm = AutoModelForCausalLM.from_pretrained(
                "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                model_file="mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                model_type="mistral",
                gpu_layers=0,
                context_length=1024,
                max_new_tokens=256,
                temperature=0.2,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.15,
                threads=4
            )
            
            self.use_llm = True
            print("✅ Mistral-7B loaded successfully!")
            
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
    
    def identify_symptoms(self, text):
        """
        FIXED: Properly identify medical symptoms (not attributes)
        """
        text_lower = text.lower()
        
        # Try LLM with BETTER prompt
        if self.use_llm and self.llm:
            try:
                # CRITICAL FIX: More explicit prompt
                prompt = f"""<s>[INST] You are a medical AI assistant. Extract ONLY the medical symptoms/conditions from this patient's description. 

DO NOT include:
- Severity descriptors (mild, severe, intense)
- Time periods (daily, weekly, 3 days)
- Intensity ratings (8/10, high, low)
- Frequencies (every morning, constant)

ONLY include actual medical symptoms like:
- headache
- nausea
- fever
- vomiting
- dizziness
- chest pain
etc.

Patient says: "{text}"

List ONLY medical symptoms, comma-separated, no other words:
[/INST]"""
                
                response = self.llm(prompt, max_new_tokens=60)
                
                # Clean response aggressively
                response = response.strip().lower()
                response = response.replace("symptoms:", "").replace("the symptoms are:", "")
                response = response.replace("medical symptoms:", "").strip()
                
                # Split and filter
                symptoms = [s.strip() for s in response.split(',')]
                
                # CRITICAL FILTER: Remove non-symptoms
                filtered = []
                invalid_words = [
                    'severe', 'mild', 'daily', 'weekly', 'every', 'morning', 'evening',
                    'day', 'days', 'week', 'weeks', 'month', 'constant', 'frequent',
                    'out of', '/10', 'intensity', 'pain level', 'worsening', 'improving',
                    'the patient', 'patient has', 'experiencing'
                ]
                
                for symptom in symptoms:
                    symptom = symptom.strip()
                    
                    # Skip if contains invalid words
                    if any(inv in symptom for inv in invalid_words):
                        continue
                    
                    # Skip if too short or too long
                    if len(symptom) < 3 or len(symptom) > 40:
                        continue
                    
                    # Skip if all numbers or punctuation
                    if not any(c.isalpha() for c in symptom):
                        continue
                    
                    filtered.append(symptom)
                
                if filtered:
                    print(f"✅ LLM identified symptoms: {filtered}")
                    return filtered[:5]  # Max 5 symptoms
                
            except Exception as e:
                print(f"⚠️ LLM symptom extraction error: {e}")
        
        # Fallback: Enhanced keyword matching
        print(f"🔍 Using keyword matching fallback")
        matched_symptoms = []
        
        # Match against knowledge base
        for symptom in self.symptoms_list:
            symptom_lower = symptom.lower().strip()
            
            # Use word boundaries for better matching
            if re.search(r'\b' + re.escape(symptom_lower) + r'\b', text_lower):
                # Additional validation: is this actually a symptom?
                if symptom_lower not in matched_symptoms:
                    matched_symptoms.append(symptom_lower)
        
        if matched_symptoms:
            print(f"✅ Keyword matching found: {matched_symptoms[:5]}")
            return matched_symptoms[:5]
        
        # Ultimate fallback
        print("⚠️ No specific symptoms detected")
        return ["general health concern"]
    
    def extract_symptom_details(self, text):
        """
        FIXED: Extract temporal/severity details (not symptoms themselves)
        """
        details = {}
        text_lower = text.lower()
        
        if self.use_llm and self.llm:
            try:
                # BETTER prompt with clear format
                prompt = f"""<s>[INST] Extract ONLY temporal and severity information from this text.

Format EXACTLY as shown:
Duration: [how long, e.g., "3 days", "2 weeks", or "Not mentioned"]
Severity: [pain scale or description, e.g., "8/10", "severe", or "Not mentioned"]
Frequency: [how often, e.g., "daily", "3 times per day", or "Not mentioned"]
Factors: [triggers/worsening factors, or "Not mentioned"]

Text: "{text}"

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
                            
                            # Clean value
                            value = value.replace('[', '').replace(']', '').strip()
                            
                            # Only keep if meaningful
                            if value and value.lower() not in ['not mentioned', 'not specified', 'n/a', 'none']:
                                details[key] = value
                
                if details:
                    print(f"✅ LLM extracted details: {details}")
                    return details
                
            except Exception as e:
                print(f"⚠️ LLM extraction error: {e}")
        
        # Regex fallback
        print(f"🔍 Using regex extraction")
        
        # Duration patterns
        duration_patterns = [
            r'for\s+(?:the\s+)?(?:past\s+)?(?:last\s+)?(\d+\s+(?:day|days|week|weeks|month|months|year|years))',
            r'(\d+\s+(?:day|days|week|weeks|month|months))\s+(?:now|ago)',
            r'since\s+(yesterday|last\s+\w+)',
        ]
        for pattern in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Duration"] = match.group(1).strip()
                break
        
        # Severity patterns
        severity_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:out\s+of|/)\s*10',
            r'\b(severe|mild|moderate|extreme|intense|terrible|unbearable|bad)\b',
        ]
        for pattern in severity_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Severity"] = match.group(1).strip()
                break
        
        # Frequency patterns
        frequency_patterns = [
            r'(every\s+(?:day|morning|evening|night|hour))',
            r'(daily|hourly|constantly|frequently)',
            r'(\d+\s+times?\s+(?:a|per)\s+(?:day|week|hour))',
        ]
        for pattern in frequency_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Frequency"] = match.group(1).strip()
                break
        
        # Factors/Triggers
        factor_patterns = [
            r'(?:worse|triggered|worsens?|aggravated)\s+(?:by|when|with|after)\s+([^.,!?]+)',
            r'(?:especially|particularly)\s+(?:in|during|when)\s+([^.,!?]+)',
        ]
        for pattern in factor_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["Factors"] = match.group(1).strip()
                break
        
        if details:
            print(f"✅ Regex extracted: {details}")
        else:
            print("⚠️ No details extracted")
        
        return details
    
    def generate_questions(self, symptom, existing_details=None):
        """
        FIXED: Generate relevant follow-up questions
        """
        if existing_details is None:
            existing_details = {}
        
        # Build context
        known_info = []
        for key, value in existing_details.items():
            if value and value != "Not specified":
                known_info.append(f"{key}: {value}")
        
        known_context = ", ".join(known_info) if known_info else "nothing"
        
        if self.use_llm and self.llm:
            try:
                prompt = f"""<s>[INST] You are a medical assistant. A patient has reported: {symptom}

We already know: {known_context}

Generate 2-3 brief follow-up questions to gather missing information. Focus on:
- Duration (if unknown)
- Severity/intensity (if unknown)
- Frequency (if unknown)
- Triggers or worsening factors (if unknown)

Format: One question per line, each under 15 words. No numbering or prefixes.

Questions:
[/INST]"""
                
                response = self.llm(prompt, max_new_tokens=120)
                
                questions = []
                for line in response.split('\n'):
                    line = line.strip()
                    # Remove numbering
                    line = re.sub(r'^\d+[\.)]\s*', '', line)
                    line = re.sub(r'^[-•]\s*', '', line)
                    
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
        
        print(f"✅ Template generated {len(questions[:3])} questions")
        return questions[:3]
    
    def summarize_patient_condition(self, patient_data):
        """
        FIXED: Generate comprehensive clinical summary
        """
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        demographic = patient_data.get("demographic", {})
        
        if not symptoms:
            return "Patient presents for general health assessment. No specific symptoms reported at this time."
        
        print(f"🤖 Generating clinical summary for {len(symptoms)} symptom(s)")
        
        if self.use_llm and self.llm:
            try:
                # Build comprehensive context
                age = demographic.get('age', 'Adult')
                gender = demographic.get('gender', 'patient')
                
                # Format symptoms with details
                symptom_descriptions = []
                for sym, details in patient_data.get("per_symptom", {}).items():
                    desc = f"- {sym.title()}"
                    detail_parts = []
                    
                    if details.get('Duration'):
                        detail_parts.append(f"duration: {details['Duration']}")
                    if details.get('Severity'):
                        detail_parts.append(f"severity: {details['Severity']}")
                    if details.get('Frequency'):
                        detail_parts.append(f"frequency: {details['Frequency']}")
                    if details.get('Factors'):
                        detail_parts.append(f"triggers: {details['Factors']}")
                    
                    if detail_parts:
                        desc += f" ({', '.join(detail_parts)})"
                    
                    symptom_descriptions.append(desc)
                
                symptom_text = "\n".join(symptom_descriptions)
                
                prompt = f"""<s>[INST] Write a professional clinical summary for a medical record.

Patient: {age}-year-old {gender}

Symptoms:
{symptom_text}

Write a 2-3 sentence clinical summary suitable for a doctor's review. Include:
1. Patient demographics
2. Main presenting symptoms with key characteristics
3. Clinical significance or concerns

Clinical summary:
[/INST]"""
                
                summary = self.llm(prompt, max_new_tokens=200)
                
                # Clean response
                summary = summary.strip()
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
        first_symptom_details = list(patient_data.get("per_symptom", {}).values())[0]
        if first_symptom_details.get('Duration'):
            summary += f"Symptoms present for {first_symptom_details['Duration']}. "
        
        summary += "Detailed symptom analysis and general health information recorded for clinical review."
        
        return summary
    
    def get_clinical_insights(self, patient_data):
        """
        FIXED: Generate comprehensive clinical insights for doctors
        """
        print(f"🧠 Generating clinical insights...")
        
        symptoms = list(patient_data.get("per_symptom", {}).keys())
        demographic = patient_data.get("demographic", {})
        
        if self.use_llm and self.llm:
            try:
                age = demographic.get('age', 'unknown')
                gender = demographic.get('gender', 'unknown')
                
                # Build symptom context
                symptom_details = []
                for sym, details in patient_data.get("per_symptom", {}).items():
                    detail_str = f"{sym.title()}:"
                    for key, value in details.items():
                        if value and value != "Not specified":
                            detail_str += f" {key}={value},"
                    symptom_details.append(detail_str)
                
                symptom_text = "\n".join(symptom_details)
                
                prompt = f"""<s>[INST] Provide brief clinical insights for this case:

Patient: {age} years old, {gender}
Symptoms:
{symptom_text}

Provide (keep under 200 words total):
1. Differential Diagnoses (top 2-3 possibilities)
2. Recommended Investigations (2-3 key tests)
3. Red Flags (1-2 warning signs to watch for)

Clinical Insights:
[/INST]"""
                
                insights = self.llm(prompt, max_new_tokens=300)
                
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
- Consider relevant diagnostic tests based on symptoms
- Monitor for any red flag symptoms

This case requires thorough evaluation by a qualified healthcare provider."""


# Global LLM manager instance
llm_manager = LLMManager()