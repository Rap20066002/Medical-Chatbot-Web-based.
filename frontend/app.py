"""
Streamlit Frontend - COMPLETE FIXED VERSION
All CLI features restored with proper LLM integration
"""

import streamlit as st
import requests
from datetime import datetime
import os
import re

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


def translate_text(text, target_lang='en'):
    """Translate text to target language"""
    if target_lang == 'en':
        return text
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/language/translate",
            json={"text": text, "source": "en", "target": target_lang}
        )
        if resp.status_code == 200:
            return resp.json()["translated"]
    except:
        pass
    return text

def detect_language_and_confirm(user_text):
    """Detect language and show confirmation dialog"""
    if len(user_text.strip()) < 10:
        return False
    
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/language/detect",
            json={"text": user_text}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            detected = data["detected"]
            lang_name = data["language_name"]
            
            if data["confidence"] == "high" and detected != st.session_state.current_language:
                st.session_state.pending_language_change = {
                    "code": detected,
                    "name": lang_name
                }
                return True
    except:
        pass
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
        if isinstance(error_data, list):
            for error in error_data:
                if 'email' in str(error.get('loc', [])):
                    return "❌ Invalid email format"
                elif 'password' in str(error.get('loc', [])):
                    return "❌ Password must be at least 6 characters"
            return "❌ Please check your input"
        if 'detail' in error_data:
            return f"❌ {error_data['detail']}"
        return "❌ An error occurred"
    except:
        return f"❌ Error: {response.status_code}"

def check_api_health():
    """Check if API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
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
    """Download PDF report"""
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    try:
        if patient_id:
            url = f"{API_BASE_URL}/api/patients/{patient_id}/pdf"
        else:
            url = f"{API_BASE_URL}/api/patients/me/pdf"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.content
        return None
    except:
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
    """Patient login"""
    st.subheader("Patient Login")
    with st.form("patient_login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if not email or not password:
                st.error("❌ Fill all fields")
                return
            try:
                response = requests.post(f"{API_BASE_URL}/api/auth/patient/login", json={"email": email, "password": password})
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.logged_in = True
                    st.session_state.user_type = "patient"
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user_email = email
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error(parse_api_error(response))
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_staff_login():
    """Staff login"""
    st.subheader("Staff Login")
    user_type = st.radio("Type:", ["Doctor", "Admin"])
    with st.form("staff_login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            endpoint = "doctor" if user_type == "Doctor" else "admin"
            try:
                response = requests.post(f"{API_BASE_URL}/api/auth/{endpoint}/login", json={"email": email, "password": password})
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.logged_in = True
                    st.session_state.user_type = endpoint
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user_email = email
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error(parse_api_error(response))
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_patient_registration():
    """FIXED REGISTRATION WITH FOLLOW-UP QUESTIONS"""
    st.subheader("📝 Register as Patient")
    
    # Initialize session state
    if 'reg_form_data' not in st.session_state:
        st.session_state.reg_form_data = {
            'name': '', 'age': 25, 'email': '', 'gender': 'Male',
            'phone': '', 'password': '', 'symptoms_desc': '', 'q1': '', 'q2': ''
        }
    
    if 'symptom_details' not in st.session_state:
        st.session_state.symptom_details = {}
    
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    
    st.info("📋 Describe your condition - AI will understand!")
    
    with st.form("patient_reg"):
        st.markdown("#### Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name*", value=st.session_state.reg_form_data['name'])
            age = st.number_input("Age*", 0, 150, value=st.session_state.reg_form_data['age'])
            email = st.text_input("Email*", value=st.session_state.reg_form_data['email'])
        with col2:
            gender = st.selectbox("Gender*", ["Male", "Female", "Other"],
                                index=["Male", "Female", "Other"].index(st.session_state.reg_form_data['gender']))
            phone = st.text_input("Phone*", value=st.session_state.reg_form_data['phone'])
            password = st.text_input("Password* (6+ chars)", type="password",
                                   value=st.session_state.reg_form_data['password'])
        
        st.markdown("#### Describe Your Condition")
        symptoms_desc = st.text_area(
            "Tell us what you're experiencing*",
            placeholder="Example: I've had severe headaches for a week, 8/10 pain, every morning, worse with screens",
            value=st.session_state.reg_form_data['symptoms_desc'],
            height=120
        )
        
        analyze = st.form_submit_button("🔍 Analyze My Symptoms")
        
        # === ANALYSIS SECTION ===
        if analyze and symptoms_desc:
            st.session_state.reg_form_data.update({
                'name': name, 'age': age, 'email': email, 'gender': gender,
                'phone': phone, 'password': password, 'symptoms_desc': symptoms_desc
            })
            
            with st.spinner("🤖 Analyzing your description..."):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/api/patients/analyze-symptoms",
                        json={"description": symptoms_desc}
                    )
                    
                    if resp.status_code == 200:
                        analysis = resp.json()
                        st.session_state.analysis_result = analysis
                        
                        # Initialize details for each symptom
                        extracted_info = analysis.get('extracted_info', {})
                        for symptom in analysis['symptoms']:
                            st.session_state.symptom_details[symptom] = {
                                "Duration": extracted_info.get("Duration", ""),
                                "Severity": extracted_info.get("Severity", ""),
                                "Frequency": extracted_info.get("Frequency", ""),
                                "Factors": extracted_info.get("Factors", ""),
                                "Additional Notes": symptoms_desc
                            }
                        
                        st.success("✅ Analysis complete!")
                        st.rerun()
                    else:
                        st.error(f"Analysis failed: {resp.status_code}")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # === DISPLAY ANALYSIS RESULTS ===
        if st.session_state.analysis_result:
            analysis = st.session_state.analysis_result
            
            st.markdown("---")
            st.markdown("### 🎯 Analysis Results")
            
            # Show detected symptoms
            st.markdown("#### Detected Symptoms")
            col1, col2 = st.columns(2)
            with col1:
                for sym in analysis['symptoms']:
                    st.success(f"✅ {sym.title()}")
            
            # Show extracted information
            with col2:
                if analysis.get('extracted_info'):
                    st.markdown("**Auto-detected:**")
                    for key, value in analysis['extracted_info'].items():
                        if value:
                            st.caption(f"• {key}: {value}")
            
            # === SHOW FOLLOW-UP QUESTIONS ===
            if analysis.get('questions'):
                st.markdown("---")
                st.markdown("### 💬 Follow-up Questions")
                st.info("Help us understand your condition better:")
                
                # Store answers in session state
                if 'question_answers' not in st.session_state:
                    st.session_state.question_answers = {}
                
                for idx, question in enumerate(analysis['questions'], 1):
                    answer = st.text_input(
                        f"**Q{idx}:** {question}",
                        key=f"qa_{idx}",
                        value=st.session_state.question_answers.get(f"q{idx}", "")
                    )
                    st.session_state.question_answers[f"q{idx}"] = answer
            
            # === SYMPTOM DETAILS SECTION ===
            st.markdown("---")
            st.markdown("### ✏️ Review & Edit Details")
            
            if len(analysis['symptoms']) > 1:
                symptom_tabs = st.tabs([s.upper() for s in analysis['symptoms']])
                
                for idx, symptom in enumerate(analysis['symptoms']):
                    with symptom_tabs[idx]:
                        current_details = st.session_state.symptom_details[symptom]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            duration = st.text_input(
                                "Duration",
                                value=current_details.get("Duration", ""),
                                key=f"dur_{symptom}"
                            )
                            severity = st.text_input(
                                "Severity (1-10)",
                                value=current_details.get("Severity", ""),
                                key=f"sev_{symptom}"
                            )
                        with col2:
                            frequency = st.text_input(
                                "Frequency",
                                value=current_details.get("Frequency", ""),
                                key=f"freq_{symptom}"
                            )
                            factors = st.text_input(
                                "Triggers/Factors",
                                value=current_details.get("Factors", ""),
                                key=f"fact_{symptom}"
                            )
                        
                        # Update session state
                        st.session_state.symptom_details[symptom].update({
                            "Duration": duration,
                            "Severity": severity,
                            "Frequency": frequency,
                            "Factors": factors
                        })
            else:
                # Single symptom
                symptom = analysis['symptoms'][0]
                current_details = st.session_state.symptom_details[symptom]
                
                col1, col2 = st.columns(2)
                with col1:
                    duration = st.text_input("Duration", value=current_details.get("Duration", ""))
                    severity = st.text_input("Severity (1-10)", value=current_details.get("Severity", ""))
                with col2:
                    frequency = st.text_input("Frequency", value=current_details.get("Frequency", ""))
                    factors = st.text_input("Triggers/Factors", value=current_details.get("Factors", ""))
                
                st.session_state.symptom_details[symptom].update({
                    "Duration": duration,
                    "Severity": severity,
                    "Frequency": frequency,
                    "Factors": factors
                })
        
        # === GENERAL HEALTH SECTION ===
        st.markdown("---")
        st.markdown("#### General Health (Optional)")
        q1 = st.text_input("Chronic conditions?", placeholder="None",
                         value=st.session_state.reg_form_data['q1'])
        q2 = st.text_input("Current medications?", placeholder="None",
                         value=st.session_state.reg_form_data['q2'])
        
        # === SUBMIT BUTTON ===
        submit = st.form_submit_button("✅ Complete Registration")
        
        if submit:
            # Validation
            if not all([name, email, phone, password, symptoms_desc]):
                st.error("❌ Fill all required fields")
                return
            
            if not validate_email(email):
                st.error("❌ Invalid email format")
                return
            
            if not validate_phone(phone):
                st.error("❌ Invalid phone (need 10+ digits)")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be 6+ characters")
                return
            
            # Build symptom data
            per_symptom = {}
            if st.session_state.analysis_result and st.session_state.symptom_details:
                for symptom in st.session_state.analysis_result['symptoms']:
                    per_symptom[symptom] = st.session_state.symptom_details.get(symptom, {
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
                    "Have you had any surgeries in the past?": "None",
                    "Do you have any allergies?": "None"
                },
                "password": password
            }
            
            # Submit registration
            try:
                with st.spinner("Creating your account..."):
                    resp = requests.post(
                        f"{API_BASE_URL}/api/auth/patient/register",
                        json=patient_data,
                        timeout=10
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
                            'phone': '', 'password': '', 'symptoms_desc': '', 'q1': '', 'q2': ''
                        }
                        st.session_state.symptom_details = {}
                        st.session_state.analysis_result = None
                        st.session_state.question_answers = {}
                        
                        st.success("✅ Registration complete! You're now logged in.")
                        st.info("🤖 AI clinical summary is being generated in the background (takes 5-7 minutes). You can view your profile now, and the summary will appear automatically when ready.")
                        st.balloons()

                        import time
                        time.sleep(2)

                        st.rerun()
                    else:
                        st.error(parse_api_error(resp))
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timeout - but this shouldn't happen now!")           
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_staff_registration():
    """Staff registration"""
    reg_type = st.radio("Register as:", ["Doctor", "Admin"])
    
    if reg_type == "Doctor":
        with st.form("doctor_reg"):
            name = st.text_input("Name*")
            email = st.text_input("Email*")
            spec = st.text_input("Specialization*")
            license = st.text_input("License*")
            password = st.text_input("Password*", type="password")
            if st.form_submit_button("Register"):
                if not all([name, email, spec, license, password]):
                    st.error("❌ Fill all fields")
                    return
                
                if not validate_email(email):
                    st.error("❌ Invalid email format. Use: user@example.com")
                    return
                
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/api/doctors/register",
                        json={"name": name, "email": email, "specialization": spec, "license_number": license, "password": password}
                    )
                    
                    if resp.status_code == 200:
                        st.success("✅ Submitted for approval!")
                    else:
                        try:
                            error_data = resp.json()
                            if 'detail' in error_data:
                                if isinstance(error_data['detail'], list):
                                    for err in error_data['detail']:
                                        if 'msg' in err:
                                            st.error(f"❌ {err['msg']}")
                                            break
                                else:
                                    st.error(f"❌ {error_data['detail']}")
                            else:
                                st.error("❌ Registration failed")
                        except:
                            st.error(f"❌ Error: {resp.status_code}")
                except Exception as e:
                    st.error(f"❌ {str(e)}")
    else:
        with st.form("admin_reg"):
            name = st.text_input("Name*")
            email = st.text_input("Email*")
            password = st.text_input("Password*", type="password")
            if st.form_submit_button("Create Admin"):
                try:
                    resp = requests.post(f"{API_BASE_URL}/api/admin/create-first", json={"name": name, "email": email, "password": password})
                    if resp.status_code == 200:
                        st.success("✅ Admin created!")
                    else:
                        st.error(parse_api_error(resp))
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def show_dashboard():
    """Route to correct dashboard"""
    if st.session_state.user_type == "patient":
        show_patient_dashboard()
    elif st.session_state.user_type == "doctor":
        show_doctor_dashboard()
    elif st.session_state.user_type == "admin":
        show_admin_dashboard()

def show_patient_dashboard():
    """ENHANCED PATIENT DASHBOARD - Complete Update Section"""
    st.title("👤 Patient Dashboard")
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    try:
        resp = requests.get(f"{API_BASE_URL}/api/patients/me", headers=headers)
        if resp.status_code != 200:
            st.error("Failed to load data")
            return
        
        patient_data = resp.json()
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Profile", "🩺 Records", "✏️ Update", "💬 Change Password"])
        
        # === TAB 1: Profile (unchanged) ===
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
        
        # === TAB 2: Records (unchanged) ===
        with tab2:
            st.subheader("🩺 Health Records")
            
            # Check summary status
            summary_status = patient_data.get("summary_status", "unknown")
            
            if summary_status == "generating":
                # Summary still being generated
                st.info("🤖 AI Clinical Summary is being generated... (takes 5-7 minutes)")
                
                # Show loading animation
                with st.spinner("Analyzing your health data with AI..."):
                    st.write("This includes:")
                    st.write("• Differential diagnoses")
                    st.write("• Clinical insights")
                    st.write("• Professional medical summary")
                
                # Auto-refresh button
                if st.button("🔄 Check if Summary is Ready", use_container_width=True):
                    st.rerun()
                
                # Auto-refresh every 30 seconds
                st.markdown("*Page will auto-refresh in 30 seconds...*")
                import time
                time.sleep(30)
                st.rerun()
                
            elif summary_status == "completed":
                # Summary ready!
                if patient_data.get("summary"):
                    st.success("✅ AI Clinical Summary (Ready)")
                    with st.expander("📋 View Clinical Summary", expanded=True):
                        st.markdown(patient_data["summary"])
                        
                        # Show when it was generated
                        if patient_data.get("summary_generated_at"):
                            from datetime import datetime
                            gen_time = datetime.fromtimestamp(patient_data["summary_generated_at"])
                            st.caption(f"Generated: {gen_time.strftime('%Y-%m-%d %H:%M')}")
            
            elif summary_status == "failed":
                st.warning("⚠️ AI summary generation failed. Your data is safe, but automated analysis is unavailable.")
            
            else:
                # Old patient without status field
                if patient_data.get("summary"):
                    st.success(patient_data["summary"])
            
            # Show symptoms (always visible)
            st.markdown("---")
            st.markdown("#### Reported Symptoms")
            for sym, det in patient_data["per_symptom"].items():
                with st.expander(f"📌 {sym.upper()}", expanded=False):
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
            
            # General health questions
            st.markdown("---")
            st.markdown("#### General Health Information")
            for question, answer in patient_data.get("gen_questions", {}).items():
                if answer and answer != "None":
                    st.write(f"**{question}**")
                    st.write(f"↳ {answer}")
        
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
                        new_gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                                                index=["Male", "Female", "Other"].index(demo['gender']))
                        new_phone = st.text_input("Phone", value=demo['phone'])
                    
                    if st.form_submit_button("💾 Update Demographics"):
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
                                    upd_resp = requests.put(f"{API_BASE_URL}/api/patients/me", headers=headers, json=update_payload)
                                    if upd_resp.status_code == 200:
                                        st.success("✅ Demographics updated!")
                                        st.rerun()
                                    else:
                                        st.error(parse_api_error(upd_resp))
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            
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
            
            with st.form("change_password"):
                current_pwd = st.text_input("Current Password", type="password")
                new_pwd = st.text_input("New Password (6+ chars)", type="password")
                confirm_pwd = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("🔒 Change Password"):
                    if not all([current_pwd, new_pwd, confirm_pwd]):
                        st.error("❌ Fill all fields")
                    elif len(new_pwd) < 6:
                        st.error("❌ Password must be 6+ characters")
                    elif new_pwd != confirm_pwd:
                        st.error("❌ Passwords don't match")
                    else:
                        pwd_resp = requests.post(
                            f"{API_BASE_URL}/api/patients/me/change-password",
                            headers=headers,
                            json={
                                "current_password": current_pwd,
                                "new_password": new_pwd
                            }
                        )
                        
                        if pwd_resp.status_code == 200:
                            st.success("✅ Password changed!")
                        else:
                            st.error(parse_api_error(pwd_resp))
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_doctor_dashboard():
    """
    COMPLETE FIXED DOCTOR DASHBOARD
    Tab 2 now includes AI Clinical Insights button
    """
    st.title("👨‍⚕️ Doctor Dashboard")
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    # Initialize session state for selected patient if not exists
    if 'selected_patient_id' not in st.session_state:
        st.session_state.selected_patient_id = None
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 All Patients", "🔍 Patient Details", "🔐 Change Password", "👤 My Profile"])
    
    # ==================== TAB 1: All Patients ====================
    with tab1:
        st.subheader("All Registered Patients")
        st.info("💡 Basic patient information - Click 'Patient Details' tab to view full records")
        
        try:
            resp = requests.get(f"{API_BASE_URL}/api/patients/", headers=headers)
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
                st.error("Failed to load patients")
        except Exception as e:
            st.error(f"Error loading patients: {str(e)}")
    
    # ==================== TAB 2: Patient Details WITH AI INSIGHTS ====================
    with tab2:
        st.subheader("🔍 Search and View Patient Details")

        # -------------------- Search Section --------------------
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            search_name = st.text_input("🔍 Search by Name", placeholder="Enter patient name...")
        with col2:
            search_email = st.text_input("📧 Search by Email", placeholder="Enter patient email...")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            search_button = st.button("🔍 Search", use_container_width=True)

        try:
            resp = requests.get(f"{API_BASE_URL}/api/patients/", headers=headers)
            if resp.status_code == 200:
                all_patients = resp.json()

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
                        st.warning("No patients found")
                else:
                    st.info("👆 Use search fields above")

                # ==================== PATIENT DETAILS ====================
                if st.session_state.get("selected_patient_id"):
                    st.markdown("---")
                    st.markdown("## 📄 Patient Details")

                    detail_resp = requests.get(
                        f"{API_BASE_URL}/api/patients/{st.session_state.selected_patient_id}",
                        headers=headers
                    )

                    if detail_resp.status_code != 200:
                        st.error("Failed to load patient details")
                        st.session_state.selected_patient_id = None
                        st.stop()

                    patient_data = detail_resp.json()
                    demo = patient_data["demographic"]

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### 👤 {demo['name']}")
                        st.caption(f"Patient ID: {st.session_state.selected_patient_id[-8:].upper()}")
                    with col2:
                        if st.button("🔙 Back to Search"):
                            st.session_state.selected_patient_id = None
                            st.rerun()

                    st.markdown("---")

                    with st.expander("👤 Demographics", expanded=True):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.info(f"Name: {demo['name']}")
                            st.info(f"Age: {demo['age']}")
                            st.info(f"Gender: {demo['gender']}")
                        with c2:
                            st.info(f"Email: {demo['email']}")
                            st.info(f"Phone: {demo['phone']}")

                    if patient_data.get("summary"):
                        with st.expander("📋 Clinical Summary", expanded=True):
                            st.success(patient_data["summary"])

                    with st.expander("🩺 Reported Symptoms", expanded=True):
                        symptoms = patient_data.get("per_symptom", {})
                        if symptoms:
                            for i, (name, d) in enumerate(symptoms.items(), 1):
                                st.markdown(f"#### {i}. {name.upper()}")
                                c1, c2 = st.columns(2)
                                with c1:
                                    if d.get("Duration"):
                                        st.write(f"⏱️ {d['Duration']}")
                                    if d.get("Severity"):
                                        st.write(f"📊 {d['Severity']}")
                                with c2:
                                    if d.get("Frequency"):
                                        st.write(f"🔄 {d['Frequency']}")
                                    if d.get("Factors"):
                                        st.write(f"⚡ {d['Factors']}")
                                if d.get("Additional Notes"):
                                    st.write(f"📝 {d['Additional Notes']}")
                                st.markdown("---")
                        else:
                            st.warning("No symptoms recorded")

                    # ==================== AI CLINICAL INSIGHTS (FROM ARTIFACT) ====================
                    st.markdown("---")
                    st.markdown("### 🧠 AI Clinical Insights")
                    st.info("💡 Differential diagnoses, investigations & red flags")

                    cache_key = f"insights_{st.session_state.selected_patient_id}"

                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button(
                            "🤖 Generate Clinical Insights",
                            use_container_width=True,
                            type="primary",
                            key="generate_insights_btn"
                        ):
                            with st.spinner("🧠 AI analyzing patient data..."):
                                try:
                                    r = requests.get(
                                        f"{API_BASE_URL}/api/patients/{st.session_state.selected_patient_id}/clinical-insights",
                                        headers=headers,
                                        timeout=60
                                    )
                                    if r.status_code == 200:
                                        data = r.json()
                                        st.session_state[cache_key] = {
                                            "insights": data["insights"],
                                            "generated_at": data.get("generated_at")
                                        }
                                        st.success("Insights generated")
                                        st.rerun()
                                    else:
                                        st.error(parse_api_error(r))
                                except Exception as e:
                                    st.error(str(e))

                    if cache_key in st.session_state:
                        cached = st.session_state[cache_key]

                        st.markdown("""
                        <style>
                        .insights-box {
                            background-color: #f4f8ff;
                            border-left: 6px solid #4c6ef5;
                            padding: 20px;
                            border-radius: 8px;
                            margin-top: 15px;
                        }
                        </style>
                        """, unsafe_allow_html=True)

                        st.markdown('<div class="insights-box">', unsafe_allow_html=True)
                        st.markdown("#### 🧠 Clinical Analysis")
                        st.markdown(cached["insights"])
                        st.markdown("</div>", unsafe_allow_html=True)

                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button("🔄 Regenerate"):
                                del st.session_state[cache_key]
                                st.rerun()
                        with c2:
                            if st.button("📋 View as Text"):
                                st.code(cached["insights"], language="markdown")
                        with c3:
                            st.success("📄 Included in PDF")

                    else:
                        st.info("Click **Generate Clinical Insights** above")

                    # ==================== PDF DOWNLOAD ====================
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
                                st.error("PDF generation failed")

            else:
                st.error("Failed to load patients")
        except Exception as e:
            st.error(str(e))

    
    # ==================== TAB 3: Change Password ====================
    with tab3:
        st.subheader("🔐 Change Password")
        st.info("💡 Update your doctor account password")
        
        with st.form("change_password_doctor"):
            current_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password (6+ chars)", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("🔒 Change Password"):
                if not all([current_pwd, new_pwd, confirm_pwd]):
                    st.error("❌ Fill all fields")
                elif len(new_pwd) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif new_pwd != confirm_pwd:
                    st.error("❌ Passwords don't match")
                else:
                    try:
                        pwd_resp = requests.post(
                            f"{API_BASE_URL}/api/doctors/change-password",
                            headers=headers,
                            json={
                                "current_password": current_pwd,
                                "new_password": new_pwd
                            }
                        )
                        
                        if pwd_resp.status_code == 200:
                            st.success("✅ Password changed successfully!")
                            st.balloons()
                        else:
                            st.error(parse_api_error(pwd_resp))
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    # ==================== TAB 4: Profile ====================
    with tab4:
        st.subheader("👤 My Profile")
        
        prof_resp = requests.get(f"{API_BASE_URL}/api/doctors/me", headers=headers)
        
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

def show_admin_dashboard():
    """COMPLETE ADMIN DASHBOARD"""
    st.title("🔑 Admin Dashboard")
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Stats & Demographics",
        "✅ Approve Doctors",
        "👨‍⚕️ Manage Doctors",
        "➕ Add Admin",
        "🔐 Change Password"
    ])
    
    # TAB 1: Stats & Patient Demographics
    with tab1:
        st.subheader("System Statistics")
        
        # Get counts
        p_resp = requests.get(f"{API_BASE_URL}/api/admin/patients/count", headers=headers)
        d_resp = requests.get(f"{API_BASE_URL}/api/admin/doctors/count", headers=headers)
        
        if p_resp.status_code == 200 and d_resp.status_code == 200:
            p_count = p_resp.json()["count"]
            d_stats = d_resp.json()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("👥 Total Patients", p_count)
            col2.metric("✅ Approved Doctors", d_stats["approved"])
            col3.metric("⏳ Pending", d_stats["pending"])
        
        st.markdown("---")
        st.subheader("👥 Patient Demographics")
        
        # Get all patients with reference IDs
        patients_resp = requests.get(f"{API_BASE_URL}/api/admin/patients/all", headers=headers)
        
        if patients_resp.status_code == 200:
            patients = patients_resp.json()
            
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
    
    # TAB 2: Approve Doctor Accounts
    with tab2:
        st.subheader("✅ Approve Doctor Accounts")
        
        pending_resp = requests.get(f"{API_BASE_URL}/api/admin/doctors/pending", headers=headers)
        
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
                            if st.button("✅ Approve", key=f"approve_{doc['id']}"):
                                approve_resp = requests.post(
                                    f"{API_BASE_URL}/api/admin/doctors/approve",
                                    headers=headers,
                                    json={"doctor_id": doc['id'], "approved": True}
                                )
                                
                                if approve_resp.status_code == 200:
                                    st.success("✅ Doctor approved!")
                                    st.rerun()
                        
                        with col2:
                            if st.button("❌ Reject", key=f"reject_{doc['id']}"):
                                reject_resp = requests.post(
                                    f"{API_BASE_URL}/api/admin/doctors/approve",
                                    headers=headers,
                                    json={"doctor_id": doc['id'], "approved": False}
                                )
                                
                                if reject_resp.status_code == 200:
                                    st.success("✅ Doctor rejected")
                                    st.rerun()
    
    # TAB 3: Manage Doctor Accounts
    with tab3:
        st.subheader("👨‍⚕️ Manage Doctor Accounts")
        
        manage_option = st.radio(
            "Select:",
            ["View All Doctors", "Search by Name", "Disable/Enable Account"],
            horizontal=True
        )
        
        if manage_option == "View All Doctors":
            all_docs_resp = requests.get(f"{API_BASE_URL}/api/admin/doctors/all", headers=headers)
            
            if all_docs_resp.status_code == 200:
                doctors = all_docs_resp.json()
                
                for doc in doctors:
                    status_icon = "🟢" if doc['status'] == "approved" else "🔴"
                    
                    with st.expander(f"{status_icon} Dr. {doc['name']} - {doc['email']} ({doc['status'].upper()})"):
                        st.write(f"**Specialization:** {doc['specialization']}")
                        st.write(f"**License:** {doc['license_number']}")
        
        elif manage_option == "Search by Name":
            search_name = st.text_input("Enter doctor name:")
            if st.button("🔍 Search") and search_name:
                search_resp = requests.get(
                    f"{API_BASE_URL}/api/admin/doctors/all",
                    headers=headers,
                    params={"search_name": search_name}
                )
                
                if search_resp.status_code == 200:
                    results = search_resp.json()
                    st.success(f"Found {len(results)} doctor(s)")
                    
                    for doc in results:
                        st.write(f"**{doc['name']}** - {doc['email']} ({doc['status']})")
        
        else:  # Disable/Enable
            all_docs_resp = requests.get(f"{API_BASE_URL}/api/admin/doctors/all", headers=headers)
            
            if all_docs_resp.status_code == 200:
                doctors = all_docs_resp.json()
                
                for doc in doctors:
                    status_icon = "🟢" if doc['status'] == "approved" else "🔴"
                    
                    with st.expander(f"{status_icon} Dr. {doc['name']} ({doc['status']})"):
                        if doc['status'] == "approved":
                            if st.button(f"🔴 Disable Dr. {doc['name']}", key=f"disable_{doc['id']}"):
                                confirm = st.checkbox(f"Confirm disable Dr. {doc['name']}?", key=f"confirm_disable_{doc['id']}")
                                if confirm:
                                    toggle_resp = requests.post(
                                        f"{API_BASE_URL}/api/admin/doctors/toggle",
                                        headers=headers,
                                        json={"doctor_id": doc['id']}
                                    )
                                    
                                    if toggle_resp.status_code == 200:
                                        st.success("✅ Doctor disabled")
                                        st.rerun()
                        else:
                            if st.button(f"🟢 Enable Dr. {doc['name']}", key=f"enable_{doc['id']}"):
                                toggle_resp = requests.post(
                                    f"{API_BASE_URL}/api/admin/doctors/toggle",
                                    headers=headers,
                                    json={"doctor_id": doc['id']}
                                )
                                
                                if toggle_resp.status_code == 200:
                                    st.success("✅ Doctor enabled")
                                    st.rerun()
    
    # TAB 4: Add Admin Account
    with tab4:
        st.subheader("➕ Add New Administrator")
        
        with st.form("add_admin"):
            new_name = st.text_input("Name*")
            new_email = st.text_input("Email*")
            new_password = st.text_input("Password* (6+ chars)", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            
            if st.form_submit_button("➕ Create Admin"):
                if not all([new_name, new_email, new_password]):
                    st.error("❌ Fill all fields")
                elif len(new_password) < 6:
                    st.error("❌ Password must be 6+ characters")
                elif new_password != confirm_password:
                    st.error("❌ Passwords don't match")
                else:
                    create_resp = requests.post(
                        f"{API_BASE_URL}/api/admin/create",
                        headers=headers,
                        json={
                            "name": new_name,
                            "email": new_email,
                            "password": new_password
                        }
                    )
                    
                    if create_resp.status_code == 200:
                        st.success("✅ New admin account created!")
                    else:
                        st.error(parse_api_error(create_resp))
    
    # TAB 5: Change Password
    with tab5:  # Adjust tab number as needed
        st.subheader("🔐 Change Password")
        st.info("💡 Update your admin account password")
        
        with st.form("change_password_admin"):
            current_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password (6+ chars)", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("🔒 Change Password"):
                if not all([current_pwd, new_pwd, confirm_pwd]):
                    st.error("❌ Fill all fields")
                elif len(new_pwd) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif new_pwd != confirm_pwd:
                    st.error("❌ Passwords don't match")
                else:
                    try:
                        pwd_resp = requests.post(
                            f"{API_BASE_URL}/api/admin/change-password",
                            headers=headers,
                            json={
                                "current_password": current_pwd,
                                "new_password": new_pwd
                            }
                        )
                        
                        if pwd_resp.status_code == 200:
                            st.success("✅ Password changed successfully!")
                            st.balloons()
                        else:
                            st.error(parse_api_error(pwd_resp))
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()