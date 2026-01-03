"""
Streamlit Frontend - COMPLETE FIXED VERSION
All CLI features restored with proper LLM integration
"""

import streamlit as st
import requests
from datetime import datetime
from requests.exceptions import RequestException
import os
import re
import time

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Health Assessment System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
        text-align: center;
        margin-bottom: 3rem;
    }
    .feature-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #000000;
    }
    .feature-card h3 {
    color: #1f77b4; /* heading color */
    }
    .feature-card p {
        color: #333333; /* paragraph color */
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-size: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'current_language' not in st.session_state:
    st.session_state.current_language = 'en'
if 'pending_language_change' not in st.session_state:
    st.session_state.pending_language_change = None
if 'extracted_info' not in st.session_state:
    st.session_state.extracted_info = {}
if 'detected_symptoms' not in st.session_state:
    st.session_state.detected_symptoms = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


def translate_text(text, target_lang='en', source_lang='auto'):
    """
    Translate text to target language
    ✅ FIXED: Better error handling, increased timeout, graceful fallback
    """
    if not text or target_lang == 'en':
        return text
    
    try:
        # ✅ FIX: Increase timeout to 15 seconds
        resp = requests.post(
            f"{API_BASE_URL}/api/language/translate",
            json={
                "text": text,
                "source": source_lang,
                "target": target_lang
            },
            timeout=15  # Increased from default 5s
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return data.get("translated", text)
        else:
            # Log error but don't break UI
            print(f"⚠️  Translation failed: {resp.status_code}")
            return text  # Return original text as fallback
    
    except requests.exceptions.Timeout:
        # ✅ FIX: Don't show error, just use original text
        print("⚠️  Translation timeout - using original text")
        return text
    
    except requests.exceptions.ConnectionError:
        print("⚠️  Translation service unavailable - using original text")
        return text
    
    except Exception as e:
        print(f"⚠️  Translation error: {str(e)} - using original text")
        return text


def detect_and_confirm_language(text, field_name=""):
        """Detect language from text and show confirmation dialog"""
        if len(text.strip()) < 10:
            return False
        
        try:
            resp = requests.post(
                f"{API_BASE_URL}/api/language/detect",
                json={"text": text},
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                detected = data["detected"]
                lang_name = data["language_name"]
                confidence = data.get("confidence", "low")
                
                # Only prompt if high confidence and different from current
                if confidence == "high" and detected != st.session_state.current_language:
                    st.session_state.pending_language_change = {
                        "code": detected,
                        "name": lang_name,
                        "triggered_by": field_name
                    }
                    return True
            else:
                # ✅ FIX: Don't show error, just skip detection
                print(f"⚠️  Language detection returned {resp.status_code}")
                return False
        
        except requests.exceptions.Timeout:
            # ✅ FIX: Silent timeout - don't disrupt user experience
            print("⚠️  Language detection timeout")
            return False
        
        except requests.exceptions.ConnectionError:
            print("⚠️  Language detection service unavailable")
            return False
        
        except Exception as e:
            print(f"⚠️  Language detection error: {str(e)}")
            return False
        
        return False

def render_language_confirmation():
    """Show language change confirmation dialog"""
    if st.session_state.pending_language_change:
        lang_info = st.session_state.pending_language_change
        
        st.warning(f"🌐 I noticed you're typing in **{lang_info['name']}**")
        st.info("Would you like to switch to that language?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"✅ Yes, switch to {lang_info['name']}", use_container_width=True):
                st.session_state.current_language = lang_info['code']
                st.session_state.pending_language_change = None
                st.success(f"Switched to {lang_info['name']}!")
                st.rerun()
        
        with col2:
            if st.button("❌ No, keep current language", use_container_width=True):
                st.session_state.pending_language_change = None
                st.info("Continuing in current language")
                st.rerun()

def render_language_selector():
    """Manual language selector in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🌐 Language")
        
        try:
            resp = requests.get(f"{API_BASE_URL}/api/language/supported")
            if resp.status_code == 200:
                langs = resp.json()["languages"]
                lang_dict = {l["name"]: l["code"] for l in langs}
                
                current_name = next(
                    (n for n, c in lang_dict.items() if c == st.session_state.current_language),
                    "English"
                )
                
                selected = st.selectbox(
                    "Select:",
                    options=list(lang_dict.keys()),
                    index=list(lang_dict.keys()).index(current_name)
                )
                
                if lang_dict[selected] != st.session_state.current_language:
                    st.session_state.current_language = lang_dict[selected]
                    st.success(f"✅ {selected}")
                    st.rerun()
        except Exception as e:
            st.error(f"Language error: {str(e)}")


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone format (10+ digits)"""
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10

def parse_api_error(response):
    """Parse API error and return user-friendly message"""
    try:
        error_data = response.json()
        
        # Handle validation errors (422)
        if response.status_code == 422:
            if isinstance(error_data, dict) and 'detail' in error_data:
                details = error_data['detail']
                
                if isinstance(details, list):
                    for error in details:
                        if isinstance(error, dict):
                            field = error.get('loc', [''])[-1] if error.get('loc') else ''
                            msg = error.get('msg', '')
                            
                            # User-friendly messages
                            if 'email' in field.lower():
                                return "❌ Invalid email format. Use: user@example.com"
                            elif 'password' in field.lower():
                                return "❌ Password must be at least 6 characters"
                            elif msg:
                                return f"❌ {field.capitalize()}: {msg}"
                    return "❌ Please check your input"
                
                elif isinstance(details, str):
                    return f"❌ {details}"
        
        # Handle other errors
        if isinstance(error_data, dict):
            if 'detail' in error_data:
                detail = error_data['detail']
                
                if isinstance(detail, str):
                    # Make common errors friendly
                    if 'already exists' in detail.lower():
                        return "❌ Email already registered. Try logging in."
                    elif 'not found' in detail.lower():
                        return "❌ Account not found. Check your credentials."
                    elif 'invalid' in detail.lower() and 'password' in detail.lower():
                        return "❌ Invalid email or password."
                    elif 'pending approval' in detail.lower():
                        return "⏳ Account pending admin approval."
                    elif 'unauthorized' in detail.lower():
                        return "❌ Unauthorized. Please login again."
                    else:
                        return f"❌ {detail}"
        
        return "❌ An error occurred. Please try again."
    
    except:
        # Fallback based on status code
        error_messages = {
            400: "❌ Invalid request. Check your input.",
            401: "❌ Authentication failed. Login again.",
            403: "❌ Access denied.",
            404: "❌ Resource not found.",
            409: "❌ Data already exists.",
            422: "❌ Invalid data format.",
            500: "❌ Server error. Try again later.",
            503: "❌ Service unavailable."
        }
        return error_messages.get(response.status_code, f"❌ Error {response.status_code}")

def check_api_health():
    """Check if API is accessible with error handling"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        return False

def logout():
    """Logout user"""
    st.session_state.logged_in = False
    st.session_state.user_type = None
    st.session_state.access_token = None
    st.session_state.user_email = None
    st.session_state.chat_history = []
    st.success("Logged out successfully!")
    st.rerun()

def download_pdf(patient_id=None):
    """Download PDF report with error handling"""
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    try:
        if patient_id:
            url = f"{API_BASE_URL}/api/patients/{patient_id}/pdf"
        else:
            url = f"{API_BASE_URL}/api/patients/me/pdf"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.content
        else:
            st.error(parse_api_error(response))
            return None
    
    except requests.exceptions.Timeout:
        st.error("⏱️ PDF generation timed out. Try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to server.")
        return None
    except Exception as e:
        st.error("❌ PDF generation failed.")
        return None

# Main page
def main():
    st.markdown('<h1 class="main-header">🏥 Medical Health Assessment System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Health Screening & Patient Management</p>', unsafe_allow_html=True)
    
    api_status = check_api_health()
    if not api_status:
        st.error("⚠️ Cannot connect to backend API")
        return
    
    st.success("✅ Backend API connected!")
    
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2913/2913133.png", width=100)
        st.title("Navigation")
        if st.session_state.logged_in:
            st.info(f"**{st.session_state.user_type.upper()}**")
            st.info(f"{st.session_state.user_email}")
            if st.button("🚪 Logout"):
                logout()
        else:
            st.info("Please login or register")
    
    if not st.session_state.logged_in:
        show_home_page()
    else:
        show_dashboard()

def show_home_page():
    """Show home page"""
    st.markdown("### 🌟 Key Features")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-card"><h3>🤖 AI Analysis</h3><p>Smart symptom detection</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-card"><h3>🔒 Encrypted</h3><p>AES-256 security</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-card"><h3>📄 PDF Reports</h3><p>Download reports</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Patient Login", "👨‍⚕️ Staff Login", "📝 Register", "👨‍⚕️ Staff Register"])
    
    with tab1:
        show_patient_login()
    with tab2:
        show_staff_login()
    with tab3:
        show_patient_registration()
    with tab4:
        show_staff_registration()

def show_patient_login():
    """Patient login with enhanced error handling"""
    st.subheader("Patient Login")
    
    with st.form("patient_login"):
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login", use_container_width=True):
            # Validation
            if not email or not password:
                st.error("❌ Please enter both email and password")
                return
            
            if not validate_email(email):
                st.error("❌ Invalid email format. Use: user@example.com")
                return
            
            # API call with error handling
            with st.spinner("Logging in..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/auth/patient/login",
                        json={"email": email, "password": password},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.logged_in = True
                        st.session_state.user_type = "patient"
                        st.session_state.access_token = data["access_token"]
                        st.session_state.user_email = email
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(parse_api_error(response))
                
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Cannot connect to server. Please check if backend is running.")
                except Exception as e:
                    st.error("❌ Login failed. Please try again.")

def show_staff_login():
    """Staff login with enhanced error handling"""
    st.subheader("Staff Login")
    user_type = st.radio("Type:", ["Doctor", "Admin"], horizontal=True)
    
    with st.form("staff_login"):
        email = st.text_input("Email", placeholder="staff@example.com")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login", use_container_width=True):
            if not email or not password:
                st.error("❌ Please enter both email and password")
                return
            
            if not validate_email(email):
                st.error("❌ Invalid email format")
                return
            
            endpoint = "doctor" if user_type == "Doctor" else "admin"
            
            with st.spinner("Authenticating..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/auth/{endpoint}/login",
                        json={"email": email, "password": password},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.logged_in = True
                        st.session_state.user_type = endpoint
                        st.session_state.access_token = data["access_token"]
                        st.session_state.user_email = email
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(parse_api_error(response))
                
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Cannot connect to server.")
                except Exception as e:
                    st.error("❌ Login failed. Please try again.")

def show_patient_registration():
    """
    ENHANCED PATIENT REGISTRATION
    - Language detection with LLM
    - Data preservation during language switch
    - Translated questions and responses
    """
    st.subheader("📝 Register as Patient")
    
    # ============================================================
    # INITIALIZE SESSION STATE FOR FORM DATA PERSISTENCE
    # ============================================================
    if 'reg_form_data' not in st.session_state:
        st.session_state.reg_form_data = {
            'name': '', 'age': 25, 'email': '', 'gender': 'Male',
            'phone': '', 'password': '', 'symptoms_desc': '', 
            'q1': '', 'q2': '', 'q3': '', 'q4': ''
        }

    if 'symptom_details' not in st.session_state:
        st.session_state.symptom_details = {}

    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None

    if 'current_language' not in st.session_state:
        st.session_state.current_language = 'en'

    if 'pending_language_change' not in st.session_state:
        st.session_state.pending_language_change = None


    # ============================================================
    # LANGUAGE CONFIRMATION DIALOG
    # ============================================================
    if st.session_state.pending_language_change:
        lang_info = st.session_state.pending_language_change
        
        st.warning(f"🌐 I noticed you're typing in **{lang_info['name']}**")
        st.info("Would you like to switch the interface to that language?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                f"✅ Yes, switch to {lang_info['name']}", 
                use_container_width=True,
                key="accept_lang_change"
            ):
                # ✅ FIX: Store old language for translation
                old_lang = st.session_state.current_language
                new_lang = lang_info['code']
                
                # Switch language
                st.session_state.current_language = new_lang
                st.session_state.pending_language_change = None
                
                # ⚡ CRITICAL FIX: Re-translate LLM questions if they exist
                if st.session_state.get("analysis_result"):
                    analysis = st.session_state.analysis_result
                    
                    # Re-translate symptom names
                    if analysis.get('symptoms') and new_lang != 'en':
                        try:
                            translated_symptoms = []
                            for sym in analysis['symptoms']:
                                translated = translate_text(
                                    sym,
                                    target_lang=new_lang,
                                    source_lang='en'
                                )
                                translated_symptoms.append(translated)
                            analysis['symptoms_translated'] = translated_symptoms
                        except Exception as e:
                            print(f"Error translating symptoms: {e}")
                    elif new_lang == 'en':
                        # Switching back to English - use original
                        analysis['symptoms_translated'] = analysis.get('symptoms', [])
                    
                    # Re-translate follow-up questions (THE KEY FIX!)
                    if analysis.get('questions') and new_lang != 'en':
                        try:
                            translated_questions = []
                            for q in analysis['questions']:
                                translated = translate_text(
                                    q,
                                    target_lang=new_lang,
                                    source_lang='en'
                                )
                                translated_questions.append(translated)
                            analysis['questions_translated'] = translated_questions
                            print(f"✅ Re-translated {len(translated_questions)} questions to {lang_info['name']}")
                        except Exception as e:
                            print(f"Error translating questions: {e}")
                            # Fallback to original English questions
                            analysis['questions_translated'] = analysis.get('questions', [])
                    elif new_lang == 'en':
                        # Switching back to English - use original
                        analysis['questions_translated'] = analysis.get('questions', [])
                    
                    # Update the stored analysis
                    st.session_state.analysis_result = analysis
                
                st.success(f"✅ Switched to {lang_info['name']}!")
                st.info("💾 All your entered data has been preserved")
                st.info("🔄 LLM-generated questions have been translated")
                time.sleep(1.5)
                st.rerun()
        
        with col2:
            if st.button(
                "❌ No, keep current language", 
                use_container_width=True,
                key="reject_lang_change"
            ):
                st.session_state.pending_language_change = None
                st.info("Continuing in current language")
                time.sleep(0.5)
                st.rerun()
        
        st.markdown("---")

    # # ============================================================
    # # LANGUAGE DETECTION HELPER
    # # ============================================================
    # def detect_and_confirm_language(text, field_name=""):
    #     """Detect language from text and show confirmation dialog"""
    #     if len(text.strip()) < 10:
    #         return False
        
    #     try:
    #         resp = requests.post(
    #             f"{API_BASE_URL}/api/language/detect",
    #             json={"text": text},
    #             timeout=5
    #         )
            
    #         if resp.status_code == 200:
    #             data = resp.json()
    #             detected = data["detected"]
    #             lang_name = data["language_name"]
    #             confidence = data.get("confidence", "low")
                
    #             # Only prompt if high confidence and different from current
    #             if confidence == "high" and detected != st.session_state.current_language:
    #                 st.session_state.pending_language_change = {
    #                     "code": detected,
    #                     "name": lang_name,
    #                     "triggered_by": field_name
    #                 }
    #                 return True
    #     except:
    #         pass
    #     return False
    
    # # ============================================================
    # # TRANSLATION HELPER
    # # ============================================================
    # def translate_text(text, target_lang='en', source_lang='auto'):
    #     """Translate text to target language"""
    #     if target_lang == 'en' or not text:
    #         return text
        
    #     try:
    #         resp = requests.post(
    #             f"{API_BASE_URL}/api/language/translate",
    #             json={
    #                 "text": text,
    #                 "source": source_lang,
    #                 "target": target_lang
    #             },
    #             timeout=10
    #         )
            
    #         if resp.status_code == 200:
    #             return resp.json()["translated"]
    #     except:
    #         pass
    #     return text
    
    # ============================================================
    # GET TRANSLATED LABELS
    # ============================================================
    def get_label(english_text):
        """
        Get translated label based on current language
        ✅ FIXED: Graceful fallback if translation fails
        """
        if st.session_state.current_language == 'en':
            return english_text
        
        # Try to translate
        translated = translate_text(
            english_text,
            st.session_state.current_language,
            source_lang='en'
        )
        
        # If translation failed, return English (better than error)
        return translated if translated else english_text
    
    # ============================================================
    # MANUAL LANGUAGE SELECTOR (SAFE & RERUN-PROOF)
    # ============================================================

    with st.expander("🌐 Change Language Manually"):
        try:
            # ----------------------------------------------------
            # Fetch supported languages from backend
            # ----------------------------------------------------
            resp = requests.get(f"{API_BASE_URL}/api/language/supported", timeout=5)
            resp.raise_for_status()  # ✅ only true API errors go to except

            langs = resp.json().get("languages", [])
            lang_dict = {l["name"]: l["code"] for l in langs}

            # ----------------------------------------------------
            # Resolve current language name
            # ----------------------------------------------------
            current_name = next(
                (n for n, c in lang_dict.items()
                if c == st.session_state.current_language),
                "English"
            )

            # ----------------------------------------------------
            # Language dropdown
            # ----------------------------------------------------
            selected = st.selectbox(
                "Select Language:",
                options=list(lang_dict.keys()),
                index=list(lang_dict.keys()).index(current_name),
                key="manual_lang_select"
            )

            # ----------------------------------------------------
            # Apply language change
            # ----------------------------------------------------
            if lang_dict[selected] != st.session_state.current_language:
                if st.button("Apply Language Change", key="apply_manual_lang"):

                    old_lang = st.session_state.current_language
                    new_lang = lang_dict[selected]

                    st.session_state.current_language = new_lang

                    # --------------------------------------------
                    # Re-translate LLM generated content (SAFE)
                    # --------------------------------------------
                    if st.session_state.get("analysis_result"):
                        analysis = st.session_state.analysis_result

                        # Translate symptoms
                        if analysis.get("symptoms"):
                            if new_lang != "en":
                                try:
                                    translated_symptoms = []
                                    for sym in analysis["symptoms"]:
                                        translated_symptoms.append(
                                            translate_text(
                                                sym,
                                                target_lang=new_lang,
                                                source_lang="en"
                                            )
                                        )
                                    analysis["symptoms_translated"] = translated_symptoms
                                except Exception:
                                    analysis["symptoms_translated"] = analysis.get("symptoms", [])
                            else:
                                analysis["symptoms_translated"] = analysis.get("symptoms", [])

                        # Translate follow-up questions
                        if analysis.get("questions"):
                            if new_lang != "en":
                                try:
                                    translated_questions = []
                                    for q in analysis["questions"]:
                                        translated_questions.append(
                                            translate_text(
                                                q,
                                                target_lang=new_lang,
                                                source_lang="en"
                                            )
                                        )
                                    analysis["questions_translated"] = translated_questions
                                except Exception:
                                    analysis["questions_translated"] = analysis.get("questions", [])
                            else:
                                analysis["questions_translated"] = analysis.get("questions", [])

                        st.session_state.analysis_result = analysis

                    # --------------------------------------------
                    # Success messages (persist-safe)
                    # --------------------------------------------
                    st.session_state.language_changed_success = True

                    st.success(f"✅ Language changed to {selected}")
                    st.info("💾 All your data is preserved")
                    st.info("🔄 Questions have been translated")

                    time.sleep(1.2)
                    st.rerun()

        # --------------------------------------------------------
        # ONLY show error if API actually failed
        # --------------------------------------------------------
        except RequestException:
            if not st.session_state.get("language_changed_success", False):
                st.error("Language service unavailable")

    
    # ============================================================
    # REGISTRATION FORM (WITH TRANSLATION)
    # ============================================================
    st.info(get_label("📋 Describe your condition - AI will understand!"))
    
    with st.form("patient_reg"):
        # Personal Information
        st.markdown(f"#### {get_label('Personal Information')}")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(
                get_label("Name") + "*",
                value=st.session_state.reg_form_data['name'],
                key="reg_name"
            )
            age = st.number_input(
                get_label("Age") + "*",
                0, 150,
                value=st.session_state.reg_form_data['age'],
                key="reg_age"
            )
            email = st.text_input(
                get_label("Email") + "*",
                value=st.session_state.reg_form_data['email'],
                placeholder="user@example.com",
                key="reg_email"
            )
        
        with col2:
            gender_options = ["Male", "Female", "Other"]
            gender_translated = [get_label(g) for g in gender_options]
            gender_index = gender_options.index(st.session_state.reg_form_data['gender'])
            
            gender_selected = st.selectbox(
                get_label("Gender") + "*",
                gender_translated,
                index=gender_index,
                key="reg_gender"
            )
            # Map back to English for storage
            gender = gender_options[gender_translated.index(gender_selected)]
            
            phone = st.text_input(
                get_label("Phone") + "*",
                value=st.session_state.reg_form_data['phone'],
                key="reg_phone"
            )
            password = st.text_input(
                get_label("Password") + "* (6+ chars)",
                type="password",
                value=st.session_state.reg_form_data['password'],
                key="reg_password"
            )
        
        # Symptoms Description
        st.markdown(f"#### {get_label('Describe Your Condition')}")
        
        symptoms_desc = st.text_area(
            get_label("Tell us what you're experiencing") + "*",
            placeholder=get_label("Example: I've had severe headaches for a week, 8/10 pain, every morning"),
            value=st.session_state.reg_form_data['symptoms_desc'],
            height=120,
            key="reg_symptoms"
        )
        
        # Detect language from symptom description
        if symptoms_desc and len(symptoms_desc) > 20:
            # Only detect if description changed
            if symptoms_desc != st.session_state.reg_form_data.get('last_checked_desc', ''):
                st.session_state.reg_form_data['last_checked_desc'] = symptoms_desc
                detect_and_confirm_language(symptoms_desc, "symptom description")
        
        # Analyze Symptoms Button
        analyze = st.form_submit_button(
            get_label("🔍 Analyze My Symptoms"),
            use_container_width=True
        )

        # Save form data
        if analyze or name or email or symptoms_desc:
            st.session_state.reg_form_data.update({
                'name': name,
                'age': age,
                'email': email,
                'gender': gender,
                'phone': phone,
                'password': password,
                'symptoms_desc': symptoms_desc
            })

        # === ANALYSIS SECTION ===
        if analyze and symptoms_desc:
            with st.spinner(get_label("🤖 Analyzing your description...")):
                try:
                    # ========================================================
                    # ✅ FIX: Detect language FIRST before analyzing
                    # ========================================================
                    detected_language = "en"  # Default
                    
                    if st.session_state.current_language != 'en':
                        # User already selected a language
                        detected_language = st.session_state.current_language
                        print(f"✅ Using user-selected language: {detected_language}")
                    else:
                        # Try to detect language from text
                        try:
                            detect_resp = requests.post(
                                f"{API_BASE_URL}/api/language/detect",
                                json={"text": symptoms_desc},
                                timeout=5
                            )
                            
                            if detect_resp.status_code == 200:
                                detect_data = detect_resp.json()
                                confidence = detect_data.get("confidence", "low")
                                
                                # Only use detected language if confidence is good
                                if confidence in ["high", "medium"]:
                                    detected_language = detect_data.get("detected", "en")
                                    print(f"✅ Detected language: {detected_language} (confidence: {confidence})")
                                else:
                                    print(f"⚠️  Low confidence detection, using English")
                            else:
                                print(f"⚠️  Detection failed, using English")
                        
                        except Exception as e:
                            print(f"⚠️  Detection error: {e}, using English")
                    
                    # ========================================================
                    # ✅ FIX: Pass detected language to analysis API
                    # ========================================================
                    print(f"📤 Sending analysis request with language: {detected_language}")
                    
                    resp = requests.post(
                        f"{API_BASE_URL}/api/patients/analyze-symptoms",
                        json={
                            "description": symptoms_desc,
                            "source_language": detected_language  # ✅ PASS ACTUAL LANGUAGE
                        },
                        timeout=None
                    )
                    
                    if resp.status_code == 200:
                        analysis = resp.json()
                        
                        # ========================================================
                        # ✅ CHECK: Verify if LLM is available
                        # ========================================================
                        try:
                            api_info = requests.get(f"{API_BASE_URL}/", timeout=5)
                            llm_available = api_info.json().get("llm_available", False) if api_info.status_code == 200 else False
                        except:
                            llm_available = False
                        
                        # ========================================================
                        # ✅ FIX: Remove questions if non-LLM mode
                        # ========================================================
                        if not llm_available:
                            print("📝 Non-LLM mode: Removing follow-up questions")
                            analysis['questions'] = []
                            analysis['questions_translated'] = []
                        
                        # Translate results back to user's language if needed
                        if st.session_state.current_language != 'en':
                            # Translate symptom names
                            translated_symptoms = []
                            for sym in analysis['symptoms']:
                                translated = translate_text(
                                    sym,
                                    target_lang=st.session_state.current_language,
                                    source_lang='en'
                                )
                                translated_symptoms.append(translated)
                            analysis['symptoms_translated'] = translated_symptoms
                            
                            # Translate questions (only if LLM mode)
                            if llm_available and analysis.get('questions'):
                                translated_questions = []
                                for q in analysis.get('questions', []):
                                    translated = translate_text(
                                        q,
                                        target_lang=st.session_state.current_language,
                                        source_lang='en'
                                    )
                                    translated_questions.append(translated)
                                analysis['questions_translated'] = translated_questions
                        else:
                            # English language - no translation needed
                            analysis['symptoms_translated'] = analysis.get('symptoms', [])
                            if llm_available:
                                analysis['questions_translated'] = analysis.get('questions', [])
                            else:
                                analysis['questions_translated'] = []
                        
                        st.session_state.analysis_result = analysis
                        
                        # Initialize symptom details
                        extracted_info = analysis.get('extracted_info', {})
                        for symptom in analysis['symptoms']:
                            st.session_state.symptom_details[symptom] = {
                                "Duration": extracted_info.get("Duration", ""),
                                "Severity": extracted_info.get("Severity", ""),
                                "Frequency": extracted_info.get("Frequency", ""),
                                "Factors": extracted_info.get("Factors", ""),
                                "Additional Notes": symptoms_desc
                            }
                        
                        st.success(get_label("✅ Analysis complete!"))
                        st.rerun()
                    else:
                        st.error(parse_api_error(resp))
                        
                except Exception as e:
                    st.error(f"{get_label('Error')}: {str(e)}")

        # === SHOW ANALYSIS RESULTS ===
        if st.session_state.analysis_result:
            analysis = st.session_state.analysis_result
            
            # Check if LLM is available
            try:
                api_info = requests.get(f"{API_BASE_URL}/", timeout=5)
                llm_available = api_info.json().get("llm_available", False) if api_info.status_code == 200 else False
            except:
                llm_available = False
            
            st.markdown("---")
            st.markdown(f"### {get_label('🎯 Analysis Results')}")
            
            # Show detected symptoms (in user's language)
            st.markdown(f"#### {get_label('Detected Symptoms')}")
            
            symptoms_to_show = analysis.get('symptoms_translated', analysis['symptoms'])
            
            col1, col2 = st.columns(2)
            with col1:
                for sym in symptoms_to_show[:len(symptoms_to_show)//2 + 1]:
                    st.success(f"✅ {sym.title()}")
            with col2:
                for sym in symptoms_to_show[len(symptoms_to_show)//2 + 1:]:
                    st.success(f"✅ {sym.title()}")
            
            # Show extracted information
            if analysis.get('extracted_info'):
                st.markdown(f"**{get_label('Auto-detected')}:**")
                for key, value in analysis['extracted_info'].items():
                    if value:
                        translated_key = get_label(key)
                        st.caption(f"• {translated_key}: {value}")
            
            # === FOLLOW-UP QUESTIONS (ONLY IN LLM MODE) ===
            if llm_available and (analysis.get('questions') or analysis.get('questions_translated')):
                st.markdown("---")
                st.markdown(f"### {get_label('💬 Follow-up Questions')}")
                st.info(get_label("Help us understand your condition better:"))
                
                questions_to_show = analysis.get('questions_translated', analysis.get('questions', []))
                
                if 'question_answers' not in st.session_state:
                    st.session_state.question_answers = {}
                
                for idx, question in enumerate(questions_to_show, 1):
                    answer = st.text_input(
                        f"**Q{idx}:** {question}",
                        key=f"qa_{idx}",
                        value=st.session_state.question_answers.get(f"q{idx}", "")
                    )
                    st.session_state.question_answers[f"q{idx}"] = answer
            
            # === SYMPTOM DETAILS (ALWAYS SHOWN) ===
            st.markdown("---")
            st.markdown(f"### {get_label('✏️ Review & Edit Details')}")
            
            if not llm_available:
                st.info(get_label("💡 Please provide details for each symptom below"))
            
            # Use English symptom names for storage, but display in user's language
            symptoms_english = analysis['symptoms']
            symptoms_display = analysis.get('symptoms_translated', symptoms_english)
            
            if len(symptoms_english) > 1:
                symptom_tabs = st.tabs([s.upper() for s in symptoms_display])
                
                for idx, (symptom_en, symptom_display) in enumerate(zip(symptoms_english, symptoms_display)):
                    with symptom_tabs[idx]:
                        current_details = st.session_state.symptom_details.get(symptom_en, {})
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            duration = st.text_input(
                                get_label("Duration"),
                                value=current_details.get("Duration", ""),
                                key=f"dur_{symptom_en}",
                                placeholder=get_label("e.g., 3 days, 1 week")
                            )
                            severity = st.text_input(
                                get_label("Severity (1-10)"),
                                value=current_details.get("Severity", ""),
                                key=f"sev_{symptom_en}",
                                placeholder="1-10"
                            )
                        with col2:
                            frequency = st.text_input(
                                get_label("Frequency"),
                                value=current_details.get("Frequency", ""),
                                key=f"freq_{symptom_en}",
                                placeholder=get_label("e.g., daily, 3 times a day")
                            )
                            factors = st.text_input(
                                get_label("Triggers/Factors"),
                                value=current_details.get("Factors", ""),
                                key=f"fact_{symptom_en}",
                                placeholder=get_label("e.g., after eating, stress")
                            )
                        
                        # Update with English keys for storage
                        st.session_state.symptom_details[symptom_en].update({
                            "Duration": duration,
                            "Severity": severity,
                            "Frequency": frequency,
                            "Factors": factors
                        })
            else:
                # Single symptom
                symptom_en = symptoms_english[0]
                current_details = st.session_state.symptom_details.get(symptom_en, {})
                
                col1, col2 = st.columns(2)
                with col1:
                    duration = st.text_input(
                        get_label("Duration"),
                        value=current_details.get("Duration", ""),
                        placeholder=get_label("e.g., 3 days, 1 week")
                    )
                    severity = st.text_input(
                        get_label("Severity (1-10)"),
                        value=current_details.get("Severity", ""),
                        placeholder="1-10"
                    )
                with col2:
                    frequency = st.text_input(
                        get_label("Frequency"),
                        value=current_details.get("Frequency", ""),
                        placeholder=get_label("e.g., daily, 3 times a day")
                    )
                    factors = st.text_input(
                        get_label("Triggers/Factors"),
                        value=current_details.get("Factors", ""),
                        placeholder=get_label("e.g., after eating, stress")
                    )
                
                st.session_state.symptom_details[symptom_en].update({
                    "Duration": duration,
                    "Severity": severity,
                    "Frequency": frequency,
                    "Factors": factors
                })
        
        # === GENERAL HEALTH QUESTIONS ===
        st.markdown("---")
        st.markdown(f"#### {get_label('General Health (Optional)')}")
        
        q1 = st.text_input(
            get_label("Do you have any chronic health conditions?"),
            placeholder=get_label("None"),
            value=st.session_state.reg_form_data.get('q1', ''),
            key="reg_q1"
        )
        q2 = st.text_input(
            get_label("Are you currently taking any medications?"),
            placeholder=get_label("None"),
            value=st.session_state.reg_form_data.get('q2', ''),
            key="reg_q2"
        )
        q3 = st.text_input(
            get_label("Have you had any surgeries in the past?"),
            placeholder=get_label("None"),
            value=st.session_state.reg_form_data.get('q3', ''),
            key="reg_q3"
        )
        q4 = st.text_input(
            get_label("Do you have any allergies?"),
            placeholder=get_label("None"),
            value=st.session_state.reg_form_data.get('q4', ''),
            key="reg_q4"
        )
        
        # Save health questions
        st.session_state.reg_form_data.update({'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4})
        
        # === SUBMIT BUTTON ===
        submit = st.form_submit_button(
            get_label("✅ Complete Registration"),
            use_container_width=True
        )
        
        if submit:
            # Validation
            if not all([name, email, phone, password, symptoms_desc]):
                st.error(get_label("❌ Fill all required fields"))
                return
            
            if not validate_email(email):
                st.error(get_label("❌ Invalid email format"))
                return
            
            if not validate_phone(phone):
                st.error(get_label("❌ Invalid phone (need 10+ digits)"))
                return
            
            if len(password) < 6:
                st.error(get_label("❌ Password must be 6+ characters"))
                return
            
            # Build per_symptom data (use English keys for backend)
            per_symptom = {}
            if st.session_state.analysis_result and st.session_state.symptom_details:
                for symptom_en in st.session_state.analysis_result['symptoms']:
                    per_symptom[symptom_en] = st.session_state.symptom_details.get(symptom_en, {
                        "Duration": "",
                        "Severity": "",
                        "Frequency": "",
                        "Factors": "",
                        "Additional Notes": symptoms_desc
                    })
            else:
                per_symptom = {
                    "General": {
                        "Duration": "",
                        "Severity": "",
                        "Frequency": "",
                        "Factors": "",
                        "Additional Notes": symptoms_desc
                    }
                }
            
            # Prepare registration data
            patient_data = {
                "demographic": {
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "email": email,
                    "phone": phone
                },
                "per_symptom": per_symptom,
                "Gen_questions": {
                    "Do you have any chronic health conditions?": q1 or "None",
                    "Are you currently taking any medications?": q2 or "None",
                    "Have you had any surgeries in the past?": q3 or "None",
                    "Do you have any allergies?": q4 or "None"
                },
                "password": password
            }
            
            # Submit registration
            try:
                with st.spinner(get_label("Creating your account...")):
                    resp = requests.post(
                        f"{API_BASE_URL}/api/auth/patient/register",
                        json=patient_data,
                        timeout=15
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.logged_in = True
                        st.session_state.user_type = "patient"
                        st.session_state.access_token = data["access_token"]
                        st.session_state.user_email = email
                        
                        # Clear form data
                        st.session_state.reg_form_data = {
                            'name': '', 'age': 25, 'email': '', 'gender': 'Male',
                            'phone': '', 'password': '', 'symptoms_desc': '',
                            'q1': '', 'q2': '', 'q3': '', 'q4': ''
                        }
                        st.session_state.symptom_details = {}
                        st.session_state.analysis_result = None
                        st.session_state.question_answers = {}
                        
                        st.success(get_label("✅ Registration complete! You're now logged in."))
                        st.info(get_label("🤖 AI summary is being generated in background (5-10 minutes)"))
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(parse_api_error(resp))
            except requests.exceptions.Timeout:
                st.error(get_label("⏱️ Request timeout - Please try again"))
            except Exception as e:
                st.error(f"{get_label('Error')}: {str(e)}")

def show_staff_registration():
    """Staff registration with enhanced error handling"""
    reg_type = st.radio("Register as:", ["Doctor", "Admin"], horizontal=True)
    
    if reg_type == "Doctor":
        with st.form("doctor_reg"):
            st.markdown("#### Doctor Registration")
            name = st.text_input("Name*", placeholder="Dr. John Doe")
            email = st.text_input("Email*", placeholder="doctor@hospital.com")
            spec = st.text_input("Specialization*", placeholder="Cardiology")
            license = st.text_input("License Number*", placeholder="MD12345")
            password = st.text_input("Password* (6+ chars)", type="password")
            confirm = st.text_input("Confirm Password*", type="password")
            
            if st.form_submit_button("Register Doctor", use_container_width=True):
                # Validation
                if not all([name, email, spec, license, password]):
                    st.error("❌ Please fill all required fields")
                    return
                
                if not validate_email(email):
                    st.error("❌ Invalid email format. Use: user@example.com")
                    return
                
                if len(password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                    return
                
                if password != confirm:
                    st.error("❌ Passwords don't match")
                    return
                
                # API call
                with st.spinner("Submitting registration..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/doctors/register",
                            json={
                                "name": name,
                                "email": email,
                                "specialization": spec,
                                "license_number": license,
                                "password": password
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ Registration submitted for admin approval!")
                            st.info("📧 You'll receive notification once approved")
                            st.balloons()
                        else:
                            st.error(parse_api_error(response))
                    
                    except requests.exceptions.Timeout:
                        st.error("⏱️ Request timed out. Please try again.")
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Cannot connect to server.")
                    except Exception as e:
                        st.error("❌ Registration failed. Please try again.")
    
    else:  # Admin registration
        with st.form("admin_reg"):
            st.markdown("#### Admin Registration")
            st.info("⚠️ Only works if no admin exists in the system")
            
            name = st.text_input("Name*", placeholder="Admin Name")
            email = st.text_input("Email*", placeholder="admin@system.com")
            password = st.text_input("Password* (6+ chars)", type="password")
            confirm = st.text_input("Confirm Password*", type="password")
            
            if st.form_submit_button("Create Admin", use_container_width=True):
                if not all([name, email, password]):
                    st.error("❌ Please fill all required fields")
                    return
                
                if not validate_email(email):
                    st.error("❌ Invalid email format")
                    return
                
                if len(password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                    return
                
                if password != confirm:
                    st.error("❌ Passwords don't match")
                    return
                
                with st.spinner("Creating admin account..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/admin/create-first",
                            json={
                                "name": name,
                                "email": email,
                                "password": password
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ Admin account created successfully!")
                            st.info("You can now login with these credentials")
                            st.balloons()
                        else:
                            st.error(parse_api_error(response))
                    
                    except requests.exceptions.Timeout:
                        st.error("⏱️ Request timed out.")
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Cannot connect to server.")
                    except Exception as e:
                        st.error("❌ Admin creation failed.")

def show_dashboard():
    """Route to correct dashboard"""
    if st.session_state.user_type == "patient":
        show_patient_dashboard()
    elif st.session_state.user_type == "doctor":
        show_doctor_dashboard()
    elif st.session_state.user_type == "admin":
        show_admin_dashboard()

def show_patient_dashboard():
    """FIXED PATIENT DASHBOARD - Auto-refresh for summary generation"""
    st.title("👤 Patient Dashboard")
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    try:
        resp = requests.get(f"{API_BASE_URL}/api/patients/me", headers=headers)
        if resp.status_code != 200:
            st.error("Failed to load data")
            return
        
        patient_data = resp.json()
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Profile", "🩺 Records", "✏️ Update", "💬 Change Password"])
        
        # TAB 1: Profile (keep existing code)
        with tab1:
            st.subheader("Personal Info")
            demo = patient_data["demographic"]
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Name:** {demo['name']}")
                st.info(f"**Age:** {demo['age']}")
            with col2:
                st.info(f"**Email:** {demo['email']}")
                st.info(f"**Phone:** {demo['phone']}")
            
            st.markdown("---")
            st.subheader("📄 Health Report")
            if st.button("📥 Download PDF Report"):
                with st.spinner("Generating..."):
                    pdf = download_pdf()
                    if pdf:
                        st.download_button("💾 Save PDF", pdf, f"{demo['name']}_Report.pdf", "application/pdf")
        
        with tab2:
            st.subheader("🩺 Health Records")
            
            # ✅ FIX: Get summary status with proper default
            summary_status = patient_data.get("summary_status", "unknown")
            
            # ============================================================
            # 🔧 FIX: Smart display based on LLM mode and status
            # ============================================================
            
            # Check if LLM is enabled
            try:
                api_info = requests.get(f"{API_BASE_URL}/", timeout=5)
                llm_available = api_info.json().get("llm_available", False) if api_info.status_code == 200 else False
            except:
                llm_available = False
            
            # CASE 1: Summary is being generated (LLM MODE ONLY)
            if summary_status == "generating" and llm_available:
                st.warning("🤖 **AI Clinical Summary is being generated...**")
                
                # Pulsing animation
                st.markdown("""
                <style>
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                .generating-text {
                    animation: pulse 2s ease-in-out infinite;
                    font-size: 1.2rem;
                    color: #ff9800;
                }
                </style>
                <div class="generating-text">⏳ AI is analyzing your health data...</div>
                """, unsafe_allow_html=True)
                
                st.info("📊 **What's happening:**")
                st.markdown("""
                - ✅ Your symptoms are being analyzed by AI
                - 🧠 Generating differential diagnoses
                - 📋 Creating professional clinical summary
                - 💊 Analyzing health patterns
                """)
                
                # Show elapsed time
                if patient_data.get("created_at"):
                    elapsed = int(time.time() - patient_data["created_at"])
                    mins = elapsed // 60
                    secs = elapsed % 60
                    st.metric("⏱️ Time Elapsed", f"{mins}m {secs}s")
                    
                    if elapsed < 300:
                        st.info("⏳ Usually takes 5-10 minutes")
                    else:
                        st.warning("⏳ Complex analysis taking longer than usual...")
                
                # Auto-refresh controls
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Check Status Now", use_container_width=True, key="check_summary_btn"):
                        st.rerun()
                
                with col2:
                    st.info("🔁 Auto-refresh: Every 15s")
                
                st.success("💡 **Tip:** Summary will appear here automatically when ready!")
                
                # ⚡ Auto-refresh every 15 seconds
                time.sleep(15)
                st.rerun()
            
            # CASE 2: Summary generation completed
            elif summary_status == "completed":
                if llm_available:
                    st.success("✅ **AI Clinical Summary Generated Successfully!**")
                else:
                    st.success("✅ **Clinical Summary Available**")
                
                if patient_data.get("summary"):
                    with st.expander("📋 View Clinical Summary", expanded=True):
                        st.markdown(patient_data["summary"])
                        
                        # Show generation details
                        if patient_data.get("summary_generated_at"):
                            gen_time = datetime.fromtimestamp(patient_data["summary_generated_at"])
                            
                            if patient_data.get("created_at"):
                                duration = int(patient_data["summary_generated_at"] - patient_data["created_at"])
                                
                                if llm_available and duration > 60:
                                    # LLM mode - show generation time
                                    duration_mins = duration // 60
                                    duration_secs = duration % 60
                                    st.caption(f"✅ Generated in {duration_mins}m {duration_secs}s on {gen_time.strftime('%Y-%m-%d %H:%M:%S')}")
                                else:
                                    # Non-LLM mode - just show date
                                    st.caption(f"Generated: {gen_time.strftime('%Y-%m-%d %H:%M:%S')}")
                            else:
                                st.caption(f"Generated: {gen_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    st.error("⚠️ Summary status is 'completed' but no summary found!")
                    st.info("This shouldn't happen. Please contact support.")
            
            # CASE 3: Summary generation failed
            elif summary_status == "failed":
                st.error("⚠️ **Summary generation failed.**")
                st.info("Don't worry - your symptom data is safe. You can view your symptoms below.")
                
                # Offer retry option
                if st.button("🔄 Retry Summary Generation", use_container_width=True, key="retry_summary_btn"):
                    with st.spinner("Retrying..."):
                        try:
                            retry_resp = requests.post(
                                f"{API_BASE_URL}/api/patients/me/regenerate-summary",
                                headers=headers,
                                timeout=10
                            )
                            
                            if retry_resp.status_code == 200:
                                st.success("✅ Summary generation restarted!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Failed to restart generation")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            # CASE 4: Old patient OR unknown status
            else:
                # Check if summary exists (for old patients registered before status tracking)
                if patient_data.get("summary"):
                    st.success("✅ Clinical Summary Available")
                    with st.expander("📋 View Summary", expanded=True):
                        st.markdown(patient_data["summary"])
                else:
                    # No summary and no generating status
                    st.info("ℹ️ No clinical summary available yet")
                    if llm_available:
                        st.caption("💡 New registrations will have AI summaries generated automatically")
                    else:
                        st.caption("💡 Clinical summaries are generated during registration")
            
            # ============================================================
            # ALWAYS SHOW: Reported Symptoms
            # ============================================================
            st.markdown("---")
            st.markdown("#### 📌 Reported Symptoms")
            
            symptoms = patient_data.get("per_symptom", {})
            if symptoms:
                for sym, det in symptoms.items():
                    with st.expander(f"📍 {sym.upper()}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            if det.get("Duration"):
                                st.write(f"**Duration:** {det['Duration']}")
                            if det.get("Severity"):
                                st.write(f"**Severity:** {det['Severity']}")
                        with col2:
                            if det.get("Frequency"):
                                st.write(f"**Frequency:** {det['Frequency']}")
                            if det.get("Factors"):
                                st.write(f"**Factors:** {det['Factors']}")
                        if det.get("Additional Notes"):
                            st.write(f"**Notes:** {det['Additional Notes']}")
            else:
                st.info("No symptoms recorded")
            
            # ============================================================
            # ALWAYS SHOW: General Health Information
            # ============================================================
            st.markdown("---")
            st.markdown("#### 🏥 General Health Information")
            
            gen_questions = patient_data.get("gen_questions", {})
            if gen_questions:
                for question, answer in gen_questions.items():
                    if answer and answer.strip() and answer.lower() != "none":
                        st.write(f"**{question}**")
                        st.write(f"↳ {answer}")
            else:
                st.info("No general health information recorded")    
        
        # === TAB 3: ENHANCED UPDATE SECTION ===
        with tab3:
            st.subheader("✏️ Update Your Information")
            
            # Use st.radio for section selection instead of expanders
            update_section = st.radio(
                "Choose what to update:",
                ["👤 Demographics", "🩺 Existing Symptoms", "➕ Add New Symptom", "🏥 General Health"],
                horizontal=True
            )
            
            st.markdown("---")
            
            # Section 1: Update Demographics
            if update_section == "👤 Demographics":
                st.markdown("### 👤 Update Personal Information")
                st.info("💡 Update any demographic field below")
                demo = patient_data["demographic"]
                
                with st.form("update_demographics"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Name", value=demo['name'])
                        new_age = st.number_input("Age", 0, 150, value=int(demo['age']))
                        new_email = st.text_input("Email", value=demo['email'])
                    with col2:
                        new_gender = st.selectbox(
                            "Gender",
                            ["Male", "Female", "Other"],
                            index=["Male", "Female", "Other"].index(demo['gender'])
                        )
                        new_phone = st.text_input("Phone", value=demo['phone'])
                    
                    if st.form_submit_button("💾 Update Demographics", use_container_width=True):
                        if not validate_email(new_email):
                            st.error("❌ Invalid email format")
                        elif not validate_phone(new_phone):
                            st.error("❌ Invalid phone (need 10+ digits)")
                        else:
                            with st.spinner("Updating..."):
                                try:
                                    update_payload = {
                                        "demographic": {
                                            "name": new_name,
                                            "age": new_age,
                                            "gender": new_gender,
                                            "email": new_email,
                                            "phone": new_phone
                                        }
                                    }
                                    upd_resp = requests.put(
                                        f"{API_BASE_URL}/api/patients/me",
                                        headers=headers,
                                        json=update_payload,
                                        timeout=10
                                    )
                                    
                                    if upd_resp.status_code == 200:
                                        st.success("✅ Demographics updated!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(parse_api_error(upd_resp))
                                
                                except requests.exceptions.Timeout:
                                    st.error("⏱️ Request timed out.")
                                except requests.exceptions.ConnectionError:
                                    st.error("🔌 Cannot connect to server.")
                                except Exception as e:
                                    st.error("❌ Update failed.")
            
            # Section 2: Update Existing Symptoms
            elif update_section == "🩺 Existing Symptoms":
                st.markdown("### 🩺 Update Existing Symptoms")
                st.info("💡 Modify details for any symptom below")
                
                current_symptoms = patient_data["per_symptom"]
                
                if not current_symptoms:
                    st.warning("No symptoms recorded yet")
                else:
                    # Use selectbox to choose which symptom to edit
                    symptom_to_edit = st.selectbox(
                        "Select symptom to update:",
                        list(current_symptoms.keys())
                    )
                    
                    if symptom_to_edit:
                        symptom_details = current_symptoms[symptom_to_edit]
                        st.markdown(f"#### Editing: **{symptom_to_edit.upper()}**")
                        
                        with st.form(f"update_symptom_{symptom_to_edit}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                duration = st.text_input("Duration", value=symptom_details.get("Duration", ""))
                                severity = st.text_input("Severity (1-10)", value=symptom_details.get("Severity", ""))
                            with col2:
                                frequency = st.text_input("Frequency", value=symptom_details.get("Frequency", ""))
                                factors = st.text_input("Triggers/Factors", value=symptom_details.get("Factors", ""))
                            
                            additional_notes = st.text_area("Additional Notes", 
                                                        value=symptom_details.get("Additional Notes", ""),
                                                        height=100)
                            
                            if st.form_submit_button(f"💾 Update {symptom_to_edit}"):
                                with st.spinner(f"Updating {symptom_to_edit}..."):
                                    try:
                                        updated_symptoms = {}
                                        for sym_name, sym_det in current_symptoms.items():
                                            if sym_name == symptom_to_edit:
                                                updated_symptoms[sym_name] = {
                                                    "Duration": duration,
                                                    "Severity": severity,
                                                    "Frequency": frequency,
                                                    "Factors": factors,
                                                    "Additional Notes": additional_notes
                                                }
                                            else:
                                                updated_symptoms[sym_name] = sym_det
                                        
                                        update_payload = {"per_symptom": updated_symptoms}
                                        upd_resp = requests.put(f"{API_BASE_URL}/api/patients/me", headers=headers, json=update_payload)
                                        
                                        if upd_resp.status_code == 200:
                                            st.success(f"✅ {symptom_to_edit} updated!")
                                            st.rerun()
                                        else:
                                            st.error(parse_api_error(upd_resp))
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
            
            # Section 3: Add New Symptom
            elif update_section == "➕ Add New Symptom":
                st.markdown("### ➕ Add New Symptom")
                st.info("💡 Describe your new symptom - AI will extract details!")
                
                with st.container():
                    st.markdown("**💡 How to describe symptoms:**")
                    st.caption("Example: 'I have nausea every morning for the past week, severity 6/10'")
                    st.caption("AI extracts: symptom, duration, severity, frequency")
                
                new_symptom_desc = st.text_area(
                    "Describe your new symptom",
                    placeholder="Example: I've been experiencing dizziness for 2 days, happens 3-4 times daily, severity 7/10, worse when standing up quickly",
                    height=120
                )
                
                if st.button("🔍 Analyze New Symptom"):
                    if not new_symptom_desc:
                        st.error("❌ Please describe your symptom")
                    else:
                        with st.spinner("🤖 Analyzing..."):
                            try:
                                analysis_resp = requests.post(
                                    f"{API_BASE_URL}/api/patients/me/add-symptom",
                                    headers=headers,
                                    json={"description": new_symptom_desc}
                                )
                                
                                if analysis_resp.status_code == 200:
                                    analysis = analysis_resp.json()
                                    st.session_state.new_symptom_analysis = analysis
                                    st.session_state.new_symptom_desc = new_symptom_desc
                                    st.success("✅ Analysis complete!")
                                    st.rerun()
                                else:
                                    st.error(parse_api_error(analysis_resp))
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                
                # Show analysis results
                if 'new_symptom_analysis' in st.session_state:
                    analysis = st.session_state.new_symptom_analysis
                    
                    st.markdown("#### 🎯 Detected Symptoms")
                    for sym in analysis['symptoms']:
                        st.write(f"• **{sym}**")
                    
                    st.markdown("#### 📊 Extracted Information")
                    extracted = analysis.get('extracted_info', {})
                    if extracted:
                        for k, v in extracted.items():
                            st.write(f"• {k}: ✅ **{v}**")
                    
                    st.markdown("#### ✍️ Complete Missing Details")
                    
                    with st.form("add_new_symptom_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            final_duration = st.text_input(
                                "Duration" + (" ✓" if "Duration" in extracted else " *"),
                                value=extracted.get("Duration", "")
                            )
                            final_severity = st.text_input(
                                "Severity (1-10)" + (" ✓" if "Severity" in extracted else " *"),
                                value=extracted.get("Severity", "")
                            )
                        with col2:
                            final_frequency = st.text_input(
                                "Frequency" + (" ✓" if "Frequency" in extracted else " *"),
                                value=extracted.get("Frequency", "")
                            )
                            final_factors = st.text_input(
                                "Triggers/Factors" + (" ✓" if "Factors" in extracted else ""),
                                value=extracted.get("Factors", "")
                            )
                        
                        if st.form_submit_button("✅ Add This Symptom"):
                            with st.spinner("Adding symptom..."):
                                try:
                                    new_symptoms = {}
                                    
                                    # Keep all existing symptoms
                                    for sym_name, sym_det in patient_data["per_symptom"].items():
                                        new_symptoms[sym_name] = sym_det
                                    
                                    # Add new symptom(s)
                                    for detected_sym in analysis['symptoms']:
                                        new_symptoms[detected_sym] = {
                                            "Duration": final_duration,
                                            "Severity": final_severity,
                                            "Frequency": final_frequency,
                                            "Factors": final_factors,
                                            "Additional Notes": st.session_state.new_symptom_desc
                                        }
                                    
                                    update_payload = {"per_symptom": new_symptoms}
                                    upd_resp = requests.put(f"{API_BASE_URL}/api/patients/me", headers=headers, json=update_payload)
                                    
                                    if upd_resp.status_code == 200:
                                        st.success("✅ New symptom added! PDF will be regenerated.")
                                        del st.session_state.new_symptom_analysis
                                        del st.session_state.new_symptom_desc
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error(parse_api_error(upd_resp))
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            
            # Section 4: Update General Health
            elif update_section == "🏥 General Health":
                st.markdown("### 🏥 Update General Health Information")
                st.info("💡 Update your general health questions")
                
                current_questions = patient_data.get("gen_questions", {})
                
                with st.form("update_general_health"):
                    q1 = st.text_input(
                        "Do you have any chronic health conditions?",
                        value=current_questions.get("Do you have any chronic health conditions?", "")
                    )
                    q2 = st.text_input(
                        "Are you currently taking any medications?",
                        value=current_questions.get("Are you currently taking any medications?", "")
                    )
                    q3 = st.text_input(
                        "Have you had any surgeries in the past?",
                        value=current_questions.get("Have you had any surgeries in the past?", "")
                    )
                    q4 = st.text_input(
                        "Do you have any allergies?",
                        value=current_questions.get("Do you have any allergies?", "")
                    )
                    
                    if st.form_submit_button("💾 Update Health Info"):
                        with st.spinner("Updating..."):
                            try:
                                update_payload = {
                                    "gen_questions": {
                                        "Do you have any chronic health conditions?": q1,
                                        "Are you currently taking any medications?": q2,
                                        "Have you had any surgeries in the past?": q3,
                                        "Do you have any allergies?": q4
                                    }
                                }
                                upd_resp = requests.put(f"{API_BASE_URL}/api/patients/me", headers=headers, json=update_payload)
                                
                                if upd_resp.status_code == 200:
                                    st.success("✅ Health information updated!")
                                    st.rerun()
                                else:
                                    st.error(parse_api_error(upd_resp))
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        
        # TAB 4: Change Password
        with tab4:
            st.subheader("🔐 Change Password")
            
            with st.form("change_password_patient"):
                current_pwd = st.text_input("Current Password", type="password")
                new_pwd = st.text_input("New Password (6+ chars)", type="password")
                confirm_pwd = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("🔒 Change Password", use_container_width=True):
                    if not all([current_pwd, new_pwd, confirm_pwd]):
                        st.error("❌ Please fill all fields")
                    elif len(new_pwd) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    elif new_pwd != confirm_pwd:
                        st.error("❌ Passwords don't match")
                    else:
                        with st.spinner("Changing password..."):
                            try:
                                pwd_resp = requests.post(
                                    f"{API_BASE_URL}/api/patients/me/change-password",
                                    headers=headers,
                                    json={
                                        "current_password": current_pwd,
                                        "new_password": new_pwd
                                    },
                                    timeout=10
                                )
                                
                                if pwd_resp.status_code == 200:
                                    st.success("✅ Password changed successfully!")
                                    st.balloons()
                                else:
                                    st.error(parse_api_error(pwd_resp))
                            
                            except requests.exceptions.Timeout:
                                st.error("⏱️ Request timed out.")
                            except requests.exceptions.ConnectionError:
                                st.error("🔌 Cannot connect to server.")
                            except Exception as e:
                                st.error("❌ Password change failed.")
    
    except Exception as e:
        st.error(f"Error loading patient data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def show_doctor_dashboard():
    """
    COMPLETE DOCTOR DASHBOARD - FIXED VERSION
    Removed non-functional Copy & Print buttons from Clinical Insights
    """
    st.title("👨‍⚕️ Doctor Dashboard")
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    # Initialize session state for selected patient
    if 'selected_patient_id' not in st.session_state:
        st.session_state.selected_patient_id = None
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 All Patients",
        "🔍 Patient Details",
        "🔐 Change Password",
        "👤 My Profile"
    ])
    
    # ==================== TAB 1: All Patients ====================
    with tab1:
        st.subheader("All Registered Patients")
        st.info("💡 Basic patient information - Click 'Patient Details' tab to view full records")
        
        try:
            resp = requests.get(
                f"{API_BASE_URL}/api/patients/",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                patients = resp.json()
                st.success(f"📊 Total Patients: {len(patients)}")
                
                if patients:
                    for idx, p in enumerate(patients, 1):
                        with st.container():
                            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                            
                            with col1:
                                st.markdown(f"**#{idx}**")
                            
                            with col2:
                                st.markdown(f"**{p['name']}**")
                                st.caption(f"Age: {p.get('age', 'N/A')} | Gender: {p.get('gender', 'N/A')}")
                            
                            with col3:
                                st.markdown(f"📧 {p.get('email', 'N/A')}")
                                st.caption(f"📱 {p.get('phone', 'N/A')}")
                            
                            with col4:
                                if p.get('created_at'):
                                    try:
                                        from datetime import datetime
                                        created = datetime.fromtimestamp(p['created_at'])
                                        st.caption(f"Registered: {created.strftime('%Y-%m-%d')}")
                                    except:
                                        pass
                            
                            st.markdown("---")
                else:
                    st.warning("No patients registered yet")
            else:
                st.error(parse_api_error(resp))
        
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to server. Please check if backend is running.")
        except Exception as e:
            st.error("❌ Failed to load patients. Please try again.")
    
    # ==================== TAB 2: Patient Details ====================
    with tab2:
        st.subheader("🔍 Search and View Patient Details")

        # Search Section
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            search_name = st.text_input("🔍 Search by Name", placeholder="Enter patient name...")
        with col2:
            search_email = st.text_input("📧 Search by Email", placeholder="Enter patient email...")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            search_button = st.button("🔍 Search", use_container_width=True)

        try:
            resp = requests.get(
                f"{API_BASE_URL}/api/patients/",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                all_patients = resp.json()

                # Filter patients
                filtered_patients = all_patients
                if search_name:
                    filtered_patients = [
                        p for p in filtered_patients
                        if search_name.lower() in p.get("name", "").lower()
                    ]
                if search_email:
                    filtered_patients = [
                        p for p in filtered_patients
                        if search_email.lower() in p.get("email", "").lower()
                    ]

                # Show search results
                if search_button or search_name or search_email:
                    st.markdown("---")
                    st.markdown(f"### 📋 Search Results ({len(filtered_patients)} found)")

                    if filtered_patients:
                        for p in filtered_patients:
                            with st.container():
                                c1, c2, c3 = st.columns([3, 2, 1])

                                with c1:
                                    st.markdown(f"**👤 {p['name']}**")
                                    st.caption(f"Age: {p.get('age')} | Gender: {p.get('gender')}")

                                with c2:
                                    st.markdown(f"📧 {p.get('email')}")
                                    st.caption(f"📱 {p.get('phone')}")

                                with c3:
                                    if st.button(
                                        "👁️ View Details",
                                        key=f"view_{p['id']}",
                                        use_container_width=True
                                    ):
                                        st.session_state.selected_patient_id = p["id"]
                                        st.rerun()
                            st.markdown("---")
                    else:
                        st.warning("No patients found matching your search")
                else:
                    st.info("👆 Use search fields above to find patients")

                # ==================== PATIENT DETAILS VIEW ====================
                if st.session_state.get("selected_patient_id"):
                    st.markdown("---")
                    st.markdown("## 📄 Patient Details")

                    try:
                        detail_resp = requests.get(
                            f"{API_BASE_URL}/api/patients/{st.session_state.selected_patient_id}",
                            headers=headers,
                            timeout=10
                        )

                        if detail_resp.status_code == 200:
                            patient_data = detail_resp.json()
                            demo = patient_data["demographic"]

                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"### 👤 {demo['name']}")
                                st.caption(f"Patient ID: {st.session_state.selected_patient_id[-8:].upper()}")
                            with col2:
                                if st.button("🔙 Back to Search", key="back_to_search"):
                                    st.session_state.selected_patient_id = None
                                    st.rerun()

                            st.markdown("---")

                            # Demographics
                            with st.expander("👤 Demographics", expanded=True):
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.info(f"**Name:** {demo['name']}")
                                    st.info(f"**Age:** {demo['age']}")
                                    st.info(f"**Gender:** {demo['gender']}")
                                with c2:
                                    st.info(f"**Email:** {demo['email']}")
                                    st.info(f"**Phone:** {demo['phone']}")

                            # Clinical Summary
                            if patient_data.get("summary"):
                                with st.expander("📋 Clinical Summary", expanded=True):
                                    st.success(patient_data["summary"])

                            # Symptoms
                            with st.expander("🩺 Reported Symptoms", expanded=True):
                                symptoms = patient_data.get("per_symptom", {})
                                if symptoms:
                                    for i, (name, d) in enumerate(symptoms.items(), 1):
                                        st.markdown(f"#### {i}. {name.upper()}")
                                        c1, c2 = st.columns(2)
                                        with c1:
                                            if d.get("Duration"):
                                                st.write(f"⏱️ Duration: {d['Duration']}")
                                            if d.get("Severity"):
                                                st.write(f"📊 Severity: {d['Severity']}")
                                        with c2:
                                            if d.get("Frequency"):
                                                st.write(f"🔄 Frequency: {d['Frequency']}")
                                            if d.get("Factors"):
                                                st.write(f"⚡ Factors: {d['Factors']}")
                                        if d.get("Additional Notes"):
                                            st.write(f"📝 Notes: {d['Additional Notes']}")
                                        st.markdown("---")
                                else:
                                    st.warning("No symptoms recorded")

                            # ==================== AI CLINICAL INSIGHTS ====================
                            st.markdown("---")
                            st.markdown("### 🧠 AI Clinical Insights")
                            
                            # Check if LLM is available
                            try:
                                api_info = requests.get(f"{API_BASE_URL}/", timeout=5)
                                llm_available = api_info.json().get("llm_available", False) if api_info.status_code == 200 else False
                            except:
                                llm_available = False
                            
                            if llm_available:
                                st.info("💡 AI-powered differential diagnoses, investigations & red flags")
                            else:
                                st.info("💡 Clinical review notes and recommended actions")

                            # Initialize insights state
                            insights_key = f"insights_{st.session_state.selected_patient_id}"
                            if insights_key not in st.session_state:
                                st.session_state[insights_key] = {
                                    "status": "not_requested",
                                    "insights": None,
                                    "start_time": None
                                }

                            current_state = st.session_state[insights_key]

                            # ============================================================
                            # REQUEST BUTTON
                            # ============================================================
                            if current_state["status"] == "not_requested":
                                col1, col2, col3 = st.columns([1, 2, 1])
                                with col2:
                                    if llm_available:
                                        button_text = "🤖 Generate AI Clinical Insights"
                                        button_help = "AI-powered differential diagnoses and recommendations"
                                    else:
                                        button_text = "📋 Generate Clinical Review Notes"
                                        button_help = "Template-based clinical review and recommendations"
                                    
                                    if st.button(
                                        button_text,
                                        use_container_width=True,
                                        type="primary",
                                        key="req_insights_btn",
                                        help=button_help
                                    ):
                                        with st.spinner("🚀 Starting analysis..."):
                                            try:
                                                r = requests.post(
                                                    f"{API_BASE_URL}/api/patients/{st.session_state.selected_patient_id}/clinical-insights",
                                                    headers=headers,
                                                    timeout=10
                                                )
                                                
                                                if r.status_code == 200:
                                                    data = r.json()
                                                    
                                                    if data["status"] == "completed":
                                                        # Already completed (cached)
                                                        st.session_state[insights_key] = {
                                                            "status": "completed",
                                                            "insights": data["insights"],
                                                            "start_time": None
                                                        }
                                                        if llm_available:
                                                            st.success("✅ AI insights ready (cached)!")
                                                        else:
                                                            st.success("✅ Clinical notes ready!")
                                                    else:
                                                        # Started generating
                                                        st.session_state[insights_key]["status"] = "generating"
                                                        st.session_state[insights_key]["start_time"] = time.time()
                                                        
                                                        if llm_available:
                                                            st.success("✅ AI analysis started!")
                                                        else:
                                                            st.success("✅ Generating clinical notes...")
                                                    
                                                    st.rerun()
                                                else:
                                                    st.error(parse_api_error(r))
                                            
                                            except requests.exceptions.Timeout:
                                                st.error("⏱️ Request timed out. Try again.")
                                            except requests.exceptions.ConnectionError:
                                                st.error("🔌 Cannot connect to server.")
                                            except Exception as e:
                                                st.error(f"❌ Error: {str(e)}")

                            # ============================================================
                            # GENERATING STATUS
                            # ============================================================
                            elif current_state["status"] == "generating":
                                if llm_available:
                                    st.warning("🤖 **AI is analyzing patient data...**")
                                    
                                    # Pulsing animation
                                    st.markdown("""
                                    <style>
                                    @keyframes pulse {
                                        0%, 100% { opacity: 1; }
                                        50% { opacity: 0.5; }
                                    }
                                    .generating-text {
                                        animation: pulse 2s ease-in-out infinite;
                                        font-size: 1.1rem;
                                        color: #ff9800;
                                    }
                                    </style>
                                    <div class="generating-text">⏳ Generating comprehensive clinical analysis...</div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.info("📊 **AI Analysis includes:**")
                                    st.markdown("""
                                    - 🔍 Differential diagnoses
                                    - 🧪 Recommended investigations
                                    - ⚠️ Red flag symptoms
                                    - 💊 Clinical considerations
                                    """)
                                    
                                    # Show elapsed time
                                    if current_state.get("start_time"):
                                        elapsed = int(time.time() - current_state["start_time"])
                                        mins = elapsed // 60
                                        secs = elapsed % 60
                                        st.metric("⏱️ Time Elapsed", f"{mins}m {secs}s")
                                        
                                        if elapsed < 300:
                                            st.info("⏳ Usually takes 5-10 minutes")
                                        else:
                                            st.warning("⏳ Complex case - taking longer than usual...")
                                else:
                                    st.info("📝 **Generating clinical review notes...**")
                                    st.caption("This should complete quickly")
                                
                                # Check status
                                try:
                                    status_resp = requests.get(
                                        f"{API_BASE_URL}/api/patients/{st.session_state.selected_patient_id}/clinical-insights",
                                        headers=headers,
                                        timeout=10
                                    )
                                    
                                    if status_resp.status_code == 200:
                                        status_data = status_resp.json()
                                        
                                        if status_data["status"] == "completed":
                                            st.session_state[insights_key] = {
                                                "status": "completed",
                                                "insights": status_data["insights"],
                                                "start_time": None
                                            }
                                            st.success("✅ Insights generated!")
                                            st.rerun()
                                        
                                        elif status_data["status"] == "generating":
                                            st.markdown("---")
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                if st.button("🔄 Check Now", use_container_width=True):
                                                    st.rerun()
                                            
                                            with col2:
                                                if llm_available:
                                                    st.info("🔁 Auto-refresh: 15s")
                                                else:
                                                    st.info("🔁 Auto-refresh: 3s")
                                            
                                            if llm_available:
                                                st.success("💡 **Tip:** Close and come back - insights will be here!")
                                                time.sleep(15)
                                            else:
                                                time.sleep(3)
                                            
                                            st.rerun()
                                        
                                        elif status_data["status"] == "failed":
                                            st.error("❌ Generation failed")
                                            st.session_state[insights_key]["status"] = "not_requested"
                                            if st.button("🔄 Try Again"):
                                                st.rerun()
                                    else:
                                        st.error(parse_api_error(status_resp))
                                
                                except requests.exceptions.Timeout:
                                    st.error("⏱️ Status check timed out.")
                                    if st.button("🔄 Retry"):
                                        st.rerun()
                                except requests.exceptions.ConnectionError:
                                    st.error("🔌 Cannot connect to server.")
                                except Exception as e:
                                    st.error(f"⚠️ Error: {str(e)}")

                            # ============================================================
                            # DISPLAY RESULTS
                            # ============================================================
                            elif current_state["status"] == "completed":
                                if llm_available:
                                    st.success("✅ **AI Clinical Insights Generated!**")
                                else:
                                    st.success("✅ **Clinical Review Notes Generated**")
                                
                                st.markdown("""
                                <style>
                                .insights-box {
                                    background: linear-gradient(135deg, #f4f8ff 0%, #e8f0ff 100%);
                                    border-left: 6px solid #4c6ef5;
                                    padding: 25px;
                                    border-radius: 12px;
                                    margin-top: 15px;
                                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                                }
                                </style>
                                """, unsafe_allow_html=True)
                                
                                st.markdown('<div class="insights-box">', unsafe_allow_html=True)
                                if llm_available:
                                    st.markdown("#### 🧠 AI Clinical Analysis")
                                else:
                                    st.markdown("#### 📋 Clinical Review Notes")
                                st.markdown(current_state["insights"])
                                st.markdown("</div>", unsafe_allow_html=True)
                                
                                # Note about insights
                                st.info("💡 **Note:** These insights are for your reference only and are NOT saved to the patient's permanent record or included in the PDF report.")
                                
                                st.markdown("---")
                                
                                # Regenerate button (centered)
                                col1, col2, col3 = st.columns([1, 1, 1])
                                
                                with col1:
                                    pass  # Empty for spacing
                                
                                with col2:
                                    if st.button(
                                        "🔄 Regenerate Insights",
                                        use_container_width=True,
                                        key="regen_insights"
                                    ):
                                        st.session_state[insights_key] = {
                                            "status": "not_requested",
                                            "insights": None,
                                            "start_time": None
                                        }
                                        st.rerun()
                                
                                with col3:
                                    pass  # Empty for spacing

                            # PDF Download
                            st.markdown("---")
                            if st.button("📄 Download PDF Report", use_container_width=True):
                                with st.spinner("Generating PDF..."):
                                    pdf = download_pdf(st.session_state.selected_patient_id)
                                    if pdf:
                                        st.download_button(
                                            "💾 Save PDF",
                                            pdf,
                                            file_name=f"{demo['name'].replace(' ', '_')}_Report.pdf",
                                            mime="application/pdf",
                                            use_container_width=True
                                        )
                        else:
                            st.error(parse_api_error(detail_resp))
                    
                    except requests.exceptions.Timeout:
                        st.error("⏱️ Request timed out. Please try again.")
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Cannot connect to server.")
                    except Exception as e:
                        st.error("❌ Failed to load patient details.")
            else:
                st.error(parse_api_error(resp))
        
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to server.")
        except Exception as e:
            st.error("❌ Failed to load patients.")
    
    # ==================== TAB 3: Change Password ====================
    with tab3:
        st.subheader("🔐 Change Password")
        st.info("💡 Update your doctor account password")
        
        with st.form("change_password_doctor"):
            current_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password (6+ chars)", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("🔒 Change Password", use_container_width=True):
                if not all([current_pwd, new_pwd, confirm_pwd]):
                    st.error("❌ Please fill all fields")
                elif len(new_pwd) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif new_pwd != confirm_pwd:
                    st.error("❌ Passwords don't match")
                else:
                    with st.spinner("Changing password..."):
                        try:
                            pwd_resp = requests.post(
                                f"{API_BASE_URL}/api/doctors/change-password",
                                headers=headers,
                                json={
                                    "current_password": current_pwd,
                                    "new_password": new_pwd
                                },
                                timeout=10
                            )
                            
                            if pwd_resp.status_code == 200:
                                st.success("✅ Password changed successfully!")
                                st.balloons()
                            else:
                                st.error(parse_api_error(pwd_resp))
                        
                        except requests.exceptions.Timeout:
                            st.error("⏱️ Request timed out. Please try again.")
                        except requests.exceptions.ConnectionError:
                            st.error("🔌 Cannot connect to server.")
                        except Exception as e:
                            st.error("❌ Password change failed. Please try again.")

    # ==================== TAB 4: Profile ====================
    with tab4:
        st.subheader("👤 My Profile")
        
        try:
            prof_resp = requests.get(
                f"{API_BASE_URL}/api/doctors/me",
                headers=headers,
                timeout=10
            )
            
            if prof_resp.status_code == 200:
                profile = prof_resp.json()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Name:** {profile['name']}")
                    st.info(f"**Email:** {profile['email']}")
                with col2:
                    st.info(f"**Specialization:** {profile['specialization']}")
                    st.info(f"**License:** {profile['license_number']}")
                
                st.info(f"**Status:** {profile['status'].upper()}")
            else:
                st.error(parse_api_error(prof_resp))
        
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to server.")
        except Exception as e:
            st.error("❌ Failed to load profile.")

def show_admin_dashboard():
    """
    COMPLETE ADMIN DASHBOARD
    All API calls with try-catch error handling
    """
    st.title("🔑 Admin Dashboard")
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Stats & Demographics",
        "✅ Approve Doctors",
        "👨‍⚕️ Manage Doctors",
        "➕ Add Admin",
        "🔐 Change Password"
    ])
    
    # ==================== TAB 1: Stats & Patient Demographics ====================
    with tab1:
        st.subheader("System Statistics")
        
        # Get counts with error handling
        try:
            p_resp = requests.get(
                f"{API_BASE_URL}/api/admin/patients/count",
                headers=headers,
                timeout=10
            )
            
            if p_resp.status_code == 200:
                p_count = p_resp.json()["count"]
            else:
                p_count = "Error"
                st.error(parse_api_error(p_resp))
        except requests.exceptions.Timeout:
            p_count = "Timeout"
            st.error("⏱️ Failed to load patient count")
        except requests.exceptions.ConnectionError:
            p_count = "No Connection"
            st.error("🔌 Cannot connect to server")
        except Exception as e:
            p_count = "Error"
        
        try:
            d_resp = requests.get(
                f"{API_BASE_URL}/api/admin/doctors/count",
                headers=headers,
                timeout=10
            )
            
            if d_resp.status_code == 200:
                d_stats = d_resp.json()
            else:
                d_stats = {"approved": "Error", "pending": "Error"}
                st.error(parse_api_error(d_resp))
        except requests.exceptions.Timeout:
            d_stats = {"approved": "Timeout", "pending": "Timeout"}
        except requests.exceptions.ConnectionError:
            d_stats = {"approved": "No Connection", "pending": "No Connection"}
        except Exception as e:
            d_stats = {"approved": "Error", "pending": "Error"}
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("👥 Total Patients", p_count)
        col2.metric("✅ Approved Doctors", d_stats.get("approved", 0))
        col3.metric("⏳ Pending Doctors", d_stats.get("pending", 0))
        
        st.markdown("---")
        st.subheader("👥 Patient Demographics")
        
        try:
            patients_resp = requests.get(
                f"{API_BASE_URL}/api/admin/patients/all",
                headers=headers,
                timeout=10
            )
            
            if patients_resp.status_code == 200:
                patients = patients_resp.json()
                
                if patients:
                    for i, p in enumerate(patients, 1):
                        with st.expander(f"Patient #{i} (Reference: {p['reference_id']})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Name:** {p['name']}")
                                st.write(f"**Age:** {p['age']}")
                                st.write(f"**Gender:** {p['gender']}")
                            with col2:
                                st.write(f"**Email:** {p['email']}")
                                st.write(f"**Phone:** {p['phone']}")
                else:
                    st.info("No patients registered yet")
            else:
                st.error(parse_api_error(patients_resp))
        
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to server.")
        except Exception as e:
            st.error("❌ Failed to load patients.")
    
    # ==================== TAB 2: Approve Doctor Accounts ====================
    with tab2:
        st.subheader("✅ Approve Doctor Accounts")
        
        try:
            pending_resp = requests.get(
                f"{API_BASE_URL}/api/admin/doctors/pending",
                headers=headers,
                timeout=10
            )
            
            if pending_resp.status_code == 200:
                pending = pending_resp.json()
                
                if not pending:
                    st.info("✅ No pending doctor accounts to approve")
                else:
                    st.warning(f"⏳ {len(pending)} doctor(s) waiting for approval")
                    
                    for doc in pending:
                        with st.expander(f"Dr. {doc['name']} - {doc['specialization']}"):
                            st.write(f"**Email:** {doc['email']}")
                            st.write(f"**License:** {doc['license_number']}")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button(
                                    "✅ Approve",
                                    key=f"approve_{doc['id']}",
                                    use_container_width=True
                                ):
                                    try:
                                        approve_resp = requests.post(
                                            f"{API_BASE_URL}/api/admin/doctors/approve",
                                            headers=headers,
                                            json={
                                                "doctor_id": doc['id'],
                                                "approved": True
                                            },
                                            timeout=10
                                        )
                                        
                                        if approve_resp.status_code == 200:
                                            st.success("✅ Doctor approved!")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(parse_api_error(approve_resp))
                                    
                                    except requests.exceptions.Timeout:
                                        st.error("⏱️ Request timed out.")
                                    except requests.exceptions.ConnectionError:
                                        st.error("🔌 Cannot connect to server.")
                                    except Exception as e:
                                        st.error("❌ Approval failed.")
                            
                            with col2:
                                if st.button(
                                    "❌ Reject",
                                    key=f"reject_{doc['id']}",
                                    use_container_width=True
                                ):
                                    try:
                                        reject_resp = requests.post(
                                            f"{API_BASE_URL}/api/admin/doctors/approve",
                                            headers=headers,
                                            json={
                                                "doctor_id": doc['id'],
                                                "approved": False
                                            },
                                            timeout=10
                                        )
                                        
                                        if reject_resp.status_code == 200:
                                            st.success("✅ Doctor rejected")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(parse_api_error(reject_resp))
                                    
                                    except requests.exceptions.Timeout:
                                        st.error("⏱️ Request timed out.")
                                    except requests.exceptions.ConnectionError:
                                        st.error("🔌 Cannot connect to server.")
                                    except Exception as e:
                                        st.error("❌ Rejection failed.")
            else:
                st.error(parse_api_error(pending_resp))
        
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to server.")
        except Exception as e:
            st.error("❌ Failed to load pending doctors.")
    
    # ==================== TAB 3: Manage Doctor Accounts ====================
    with tab3:
        st.subheader("👨‍⚕️ Manage Doctor Accounts")
        
        manage_option = st.radio(
            "Select Action:",
            ["View All Doctors", "Search by Name", "Disable/Enable Account"],
            horizontal=True
        )
        
        if manage_option == "View All Doctors":
            try:
                all_docs_resp = requests.get(
                    f"{API_BASE_URL}/api/admin/doctors/all",
                    headers=headers,
                    timeout=10
                )
                
                if all_docs_resp.status_code == 200:
                    doctors = all_docs_resp.json()
                    
                    if doctors:
                        for doc in doctors:
                            status_icon = "🟢" if doc['status'] == "approved" else "🔴"
                            
                            with st.expander(f"{status_icon} Dr. {doc['name']} - {doc['email']} ({doc['status'].upper()})"):
                                st.write(f"**Specialization:** {doc['specialization']}")
                                st.write(f"**License:** {doc['license_number']}")
                                st.write(f"**Status:** {doc['status'].upper()}")
                    else:
                        st.info("No doctors registered yet")
                else:
                    st.error(parse_api_error(all_docs_resp))
            
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Cannot connect to server.")
            except Exception as e:
                st.error("❌ Failed to load doctors.")
        
        elif manage_option == "Search by Name":
            search_name = st.text_input("Enter doctor name:", key="search_doctor_name")
            
            if st.button("🔍 Search", key="search_doctor_btn") and search_name:
                try:
                    search_resp = requests.get(
                        f"{API_BASE_URL}/api/admin/doctors/all",
                        headers=headers,
                        params={"search_name": search_name},
                        timeout=10
                    )
                    
                    if search_resp.status_code == 200:
                        results = search_resp.json()
                        
                        if results:
                            st.success(f"Found {len(results)} doctor(s)")
                            for doc in results:
                                st.write(f"**{doc['name']}** - {doc['email']} ({doc['status']})")
                        else:
                            st.warning("No doctors found matching your search")
                    else:
                        st.error(parse_api_error(search_resp))
                
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out.")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Cannot connect to server.")
                except Exception as e:
                    st.error("❌ Search failed.")
        
        else:  # Disable/Enable
            try:
                all_docs_resp = requests.get(
                    f"{API_BASE_URL}/api/admin/doctors/all",
                    headers=headers,
                    timeout=10
                )
                
                if all_docs_resp.status_code == 200:
                    doctors = all_docs_resp.json()
                    
                    if doctors:
                        for doc in doctors:
                            status_icon = "🟢" if doc['status'] == "approved" else "🔴"
                            
                            with st.expander(f"{status_icon} Dr. {doc['name']} ({doc['status']})"):
                                st.write(f"**Email:** {doc['email']}")
                                st.write(f"**Specialization:** {doc['specialization']}")
                                
                                if doc['status'] == "approved":
                                    if st.button(
                                        f"🔴 Disable Dr. {doc['name']}",
                                        key=f"disable_{doc['id']}"
                                    ):
                                        try:
                                            toggle_resp = requests.post(
                                                f"{API_BASE_URL}/api/admin/doctors/toggle",
                                                headers=headers,
                                                json={"doctor_id": doc['id']},
                                                timeout=10
                                            )
                                            
                                            if toggle_resp.status_code == 200:
                                                st.success("✅ Doctor disabled")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(parse_api_error(toggle_resp))
                                        
                                        except requests.exceptions.Timeout:
                                            st.error("⏱️ Request timed out.")
                                        except requests.exceptions.ConnectionError:
                                            st.error("🔌 Cannot connect to server.")
                                        except Exception as e:
                                            st.error("❌ Action failed.")
                                else:
                                    if st.button(
                                        f"🟢 Enable Dr. {doc['name']}",
                                        key=f"enable_{doc['id']}"
                                    ):
                                        try:
                                            toggle_resp = requests.post(
                                                f"{API_BASE_URL}/api/admin/doctors/toggle",
                                                headers=headers,
                                                json={"doctor_id": doc['id']},
                                                timeout=10
                                            )
                                            
                                            if toggle_resp.status_code == 200:
                                                st.success("✅ Doctor enabled")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(parse_api_error(toggle_resp))
                                        
                                        except requests.exceptions.Timeout:
                                            st.error("⏱️ Request timed out.")
                                        except requests.exceptions.ConnectionError:
                                            st.error("🔌 Cannot connect to server.")
                                        except Exception as e:
                                            st.error("❌ Action failed.")
                    else:
                        st.info("No doctors to manage")
                else:
                    st.error(parse_api_error(all_docs_resp))
            
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Cannot connect to server.")
            except Exception as e:
                st.error("❌ Failed to load doctors.")
    
    # ==================== TAB 4: Add Admin Account ====================
    with tab4:
        st.subheader("➕ Add New Administrator")
        
        with st.form("add_admin"):
            new_name = st.text_input("Name*", placeholder="Admin Name")
            new_email = st.text_input("Email*", placeholder="admin@system.com")
            new_password = st.text_input("Password* (6+ chars)", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            
            if st.form_submit_button("➕ Create Admin", use_container_width=True):
                if not all([new_name, new_email, new_password]):
                    st.error("❌ Please fill all required fields")
                elif not validate_email(new_email):
                    st.error("❌ Invalid email format")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif new_password != confirm_password:
                    st.error("❌ Passwords don't match")
                else:
                    with st.spinner("Creating admin account..."):
                        try:
                            create_resp = requests.post(
                                f"{API_BASE_URL}/api/admin/create",
                                headers=headers,
                                json={
                                    "name": new_name,
                                    "email": new_email,
                                    "password": new_password
                                },
                                timeout=10
                            )
                            
                            if create_resp.status_code == 200:
                                st.success("✅ New admin account created successfully!")
                                st.balloons()
                            else:
                                st.error(parse_api_error(create_resp))
                        
                        except requests.exceptions.Timeout:
                            st.error("⏱️ Request timed out. Please try again.")
                        except requests.exceptions.ConnectionError:
                            st.error("🔌 Cannot connect to server.")
                        except Exception as e:
                            st.error("❌ Admin creation failed. Please try again.")
    
    # ==================== TAB 5: Change Password ====================
    with tab5:
        st.subheader("🔐 Change Password")
        st.info("💡 Update your admin account password")
        
        with st.form("change_password_admin"):
            current_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password (6+ chars)", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("🔒 Change Password", use_container_width=True):
                if not all([current_pwd, new_pwd, confirm_pwd]):
                    st.error("❌ Please fill all fields")
                elif len(new_pwd) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif new_pwd != confirm_pwd:
                    st.error("❌ Passwords don't match")
                else:
                    with st.spinner("Changing password..."):
                        try:
                            pwd_resp = requests.post(
                                f"{API_BASE_URL}/api/admin/change-password",
                                headers=headers,
                                json={
                                    "current_password": current_pwd,
                                    "new_password": new_pwd
                                },
                                timeout=10
                            )
                            
                            if pwd_resp.status_code == 200:
                                st.success("✅ Password changed successfully!")
                                st.balloons()
                            else:
                                st.error(parse_api_error(pwd_resp))
                        
                        except requests.exceptions.Timeout:
                            st.error("⏱️ Request timed out. Please try again.")
                        except requests.exceptions.ConnectionError:
                            st.error("🔌 Cannot connect to server.")
                        except Exception as e:
                            st.error("❌ Password change failed. Please try again.")

if __name__ == "__main__":
    main()