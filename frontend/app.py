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
    """FREE-FORM REGISTRATION"""
    st.subheader("Register as Patient")
    st.info("📋 Describe your condition - AI will understand!")
    
    with st.expander("💡 How it works"):
        st.markdown("""
        **Just describe your symptoms naturally:**
        - "I have severe headache for 3 days, 8/10 pain, daily in morning"
        - AI extracts: symptom, duration, severity, frequency
        - You only answer missing information
        """)
    
    with st.form("patient_reg"):
        st.markdown("#### Personal Info")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name*")
            age = st.number_input("Age*", 0, 150, 25)
            email = st.text_input("Email*")
        with col2:
            gender = st.selectbox("Gender*", ["Male", "Female", "Other"])
            phone = st.text_input("Phone*")
            password = st.text_input("Password*", type="password")
        
        st.markdown("#### Describe Your Condition")
        symptoms_desc = st.text_area(
            "Tell us what you're experiencing*",
            placeholder="Example: I've had severe headaches for a week, 8/10 pain, every morning, worse with screens",
            height=150
        )
        
        analyze = st.form_submit_button("🔍 Analyze Description")
        
        if analyze and symptoms_desc:
            with st.spinner("🤖 Analyzing..."):
                try:
                    resp = requests.post(f"{API_BASE_URL}/api/patients/analyze-symptoms", json={"description": symptoms_desc})
                    if resp.status_code == 200:
                        analysis = resp.json()
                        st.session_state.detected_symptoms = analysis['symptoms']
                        st.session_state.extracted_info = analysis.get('extracted_info', {})
                        st.success("✅ Analysis complete!")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Symptoms:**")
                            for s in st.session_state.detected_symptoms:
                                st.write(f"• {s}")
                        with col2:
                            st.markdown("**Extracted:**")
                            for k, v in st.session_state.extracted_info.items():
                                st.write(f"• {k}: {v}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        if st.session_state.detected_symptoms:
            st.markdown("#### Fill Missing Info")
            extracted = st.session_state.extracted_info
            col1, col2 = st.columns(2)
            with col1:
                duration = st.text_input("Duration" + (" ✓" if "Duration" in extracted else ""), value=extracted.get("Duration", ""))
                severity = st.text_input("Severity" + (" ✓" if "Severity" in extracted else ""), value=extracted.get("Severity", ""))
            with col2:
                frequency = st.text_input("Frequency" + (" ✓" if "Frequency" in extracted else ""), value=extracted.get("Frequency", ""))
                factors = st.text_input("Factors" + (" ✓" if "Factors" in extracted else ""), value=extracted.get("Factors", ""))
        
        st.markdown("#### General Health (Optional)")
        q1 = st.text_input("Chronic conditions?", placeholder="None")
        q2 = st.text_input("Current medications?", placeholder="None")
        
        submit = st.form_submit_button("✅ Complete Registration")
        
        if submit:
            if not all([name, email, phone, password, symptoms_desc]):
                st.error("❌ Fill required fields")
                return
            if not validate_email(email) or not validate_phone(phone):
                st.error("❌ Invalid email/phone")
                return
            
            per_symptom = {}
            if st.session_state.detected_symptoms:
                for sym in st.session_state.detected_symptoms:
                    per_symptom[sym] = {
                        "Duration": duration or "Not specified",
                        "Severity": severity or "Not specified",
                        "Frequency": frequency or "Not specified",
                        "Factors": factors or "Not specified",
                        "Additional Notes": symptoms_desc
                    }
            else:
                per_symptom = {"General": {"Duration": "", "Severity": "", "Frequency": "", "Factors": "", "Additional Notes": symptoms_desc}}
            
            patient_data = {
                "demographic": {"name": name, "age": age, "gender": gender, "email": email, "phone": phone},
                "per_symptom": per_symptom,
                "Gen_questions": {
                    "Do you have any chronic health conditions?": q1 or "None",
                    "Are you currently taking any medications?": q2 or "None",
                    "Have you had any surgeries in the past?": "None",
                    "Do you have any allergies?": "None"
                },
                "password": password
            }
            
            try:
                with st.spinner("Creating account..."):
                    resp = requests.post(f"{API_BASE_URL}/api/auth/patient/register", json=patient_data, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.logged_in = True
                        st.session_state.user_type = "patient"
                        st.session_state.access_token = data["access_token"]
                        st.session_state.user_email = email
                        st.success("✅ Registration complete!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(parse_api_error(resp))
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
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Profile", "🩺 Records", "✏️ Update", "💬 Chat"])
        
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
            st.subheader("Health Records")
            if patient_data.get("summary"):
                st.success(patient_data["summary"])
            st.markdown("#### Symptoms")
            for sym, det in patient_data["per_symptom"].items():
                with st.expander(f"📌 {sym}"):
                    for k, v in det.items():
                        if v and v != "Not specified":
                            st.write(f"**{k}:** {v}")
        
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
        
        # === TAB 4: Chat (unchanged) ===
        with tab4:
            st.subheader("💬 Chat Assistant")
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    st.markdown(f"**You:** {msg['content']}")
                else:
                    st.markdown(f"**Assistant:** {msg['content']}")
            
            user_msg = st.text_input("Message:")
            if st.button("Send") and user_msg:
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                with st.spinner("Thinking..."):
                    try:
                        chat_resp = requests.post(f"{API_BASE_URL}/api/patients/chat", headers=headers, json={"message": user_msg})
                        if chat_resp.status_code == 200:
                            bot_msg = chat_resp.json()['response']
                            st.session_state.chat_history.append({"role": "assistant", "content": bot_msg})
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_doctor_dashboard():
    """DOCTOR DASHBOARD with PDF downloads"""
    st.title("👨‍⚕️ Doctor Dashboard")
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    tab1, tab2 = st.tabs(["📊 All Patients", "🔍 Patient Details"])
    
    with tab1:
        try:
            resp = requests.get(f"{API_BASE_URL}/api/patients/", headers=headers)
            if resp.status_code == 200:
                patients = resp.json()
                st.success(f"Total: {len(patients)}")
                for p in patients:
                    with st.expander(f"{p['name']} - {p.get('email')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"Age: {p.get('age')}")
                        with col2:
                            if st.button("View Details", key=p['id']):
                                st.session_state.selected_patient = p['id']
                                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        if 'selected_patient' in st.session_state:
            try:
                detail = requests.get(f"{API_BASE_URL}/api/patients/{st.session_state.selected_patient}", headers=headers)
                if detail.status_code == 200:
                    data = detail.json()
                    st.markdown("### Demographics")
                    demo = data["demographic"]
                    st.info(f"Name: {demo['name']}, Age: {demo['age']}")
                    st.markdown("### Symptoms")
                    for sym, det in data["per_symptom"].items():
                        with st.expander(sym):
                            for k, v in det.items():
                                st.write(f"**{k}:** {v}")
                    if st.button("📥 Download PDF"):
                        pdf = download_pdf(st.session_state.selected_patient)
                        if pdf:
                            st.download_button("💾 Save", pdf, f"{demo['name']}_Report.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.info("Select a patient from the list")

def show_admin_dashboard():
    """ADMIN DASHBOARD"""
    st.title("🔑 Admin Dashboard")
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    tab1, tab2 = st.tabs(["📊 Stats", "👨‍⚕️ Doctors"])
    
    with tab1:
        try:
            p_resp = requests.get(f"{API_BASE_URL}/api/admin/patients/count", headers=headers)
            d_resp = requests.get(f"{API_BASE_URL}/api/admin/doctors/count", headers=headers)
            if p_resp.status_code == 200:
                st.metric("Patients", p_resp.json()["count"])
            if d_resp.status_code == 200:
                data = d_resp.json()
                col1, col2 = st.columns(2)
                col1.metric("Approved Doctors", data["approved"])
                col2.metric("Pending", data["pending"])
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Manage Doctors")
        try:
            resp = requests.get(f"{API_BASE_URL}/api/admin/doctors/all", headers=headers)
            if resp.status_code == 200:
                doctors = resp.json()
                for doc in doctors:
                    with st.expander(f"{doc['name']} - {doc['status']}"):
                        st.write(f"Email: {doc['email']}")
                        st.write(f"Specialization: {doc['specialization']}")
                        col1, col2 = st.columns(2)
                        if doc['status'] == 'pending':
                            if col1.button("✅ Approve", key=f"app_{doc['id']}"):
                                requests.post(f"{API_BASE_URL}/api/admin/doctors/approve", headers=headers, json={"doctor_id": doc['id'], "approved": True})
                                st.rerun()
                            if col2.button("❌ Reject", key=f"rej_{doc['id']}"):
                                requests.post(f"{API_BASE_URL}/api/admin/doctors/approve", headers=headers, json={"doctor_id": doc['id'], "approved": False})
                                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()