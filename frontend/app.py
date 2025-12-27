"""
Streamlit Frontend - FIXED ERROR HANDLING VERSION
Medical Health Assessment Chatbot UI with user-friendly error messages
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
        
        # Check if it's a validation error
        if isinstance(error_data, list):
            for error in error_data:
                if error.get('type') == 'value_error' and 'email' in str(error.get('loc', [])):
                    return "❌ Invalid email format. Please use format: user@example.com"
                elif 'password' in str(error.get('loc', [])):
                    return "❌ Password must be at least 6 characters long"
            return "❌ Please check your input fields and try again"
        
        # Check for detail message
        if 'detail' in error_data:
            return f"❌ {error_data['detail']}"
        
        return "❌ An error occurred. Please try again."
    except:
        return f"❌ Error: {response.status_code} - Please check your input"

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
    st.success("Logged out successfully!")
    st.rerun()

# Main page
def main():
    # Header
    st.markdown('<h1 class="main-header">🏥 Medical Health Assessment System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Health Screening & Patient Management</p>', unsafe_allow_html=True)
    
    # Check API status
    api_status = check_api_health()
    
    if not api_status:
        st.error("⚠️ Cannot connect to backend API. Please ensure the API server is running on port 8000.")
        st.code("Run: cd backend && uvicorn main:app --reload", language="bash")
        return
    
    # Show success message
    st.success("✅ Backend API is connected and healthy!")
    
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2913/2913133.png", width=100)
        st.title("Navigation")
        
        if st.session_state.logged_in:
            st.info(f"Logged in as: **{st.session_state.user_type.upper()}**")
            st.info(f"Email: {st.session_state.user_email}")
            
            if st.button("🚪 Logout"):
                logout()
        else:
            st.info("Please login or register to continue")
    
    # Main content
    if not st.session_state.logged_in:
        show_home_page()
    else:
        show_dashboard()

def show_home_page():
    """Show home page with login/register options"""
    
    # Features section
    st.markdown("### 🌟 Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🤖 AI-Powered Assessment</h3>
            <p>Intelligent symptom analysis using AI</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🔒 Secure & Encrypted</h3>
            <p>AES-256 encryption for all patient data</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🌍 Multi-Language</h3>
            <p>Support for multiple languages worldwide</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Login/Register tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Patient Login", 
        "👨‍⚕️ Staff Login", 
        "📝 Patient Registration",
        "👨‍⚕️ Doctor/Admin Registration"
    ])
    
    with tab1:
        show_patient_login()
    
    with tab2:
        show_staff_login()
    
    with tab3:
        show_patient_registration()
    
    with tab4:
        show_staff_registration()

def show_patient_login():
    """Patient login form"""
    st.subheader("Patient Login")
    
    with st.form("patient_login_form"):
        email = st.text_input("Email", placeholder="patient@example.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not email or not password:
                st.error("❌ Please fill in all fields")
                return
            
            if not validate_email(email):
                st.error("❌ Invalid email format. Use: user@example.com")
                return
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/auth/patient/login",
                    json={"email": email, "password": password}
                )
                
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
                st.error(f"❌ Connection error: {str(e)}")

def show_staff_login():
    """Doctor/Admin login form"""
    st.subheader("Doctor & Admin Login")
    
    user_type = st.radio("Select user type:", ["Doctor", "Admin"])
    
    with st.form("staff_login_form"):
        email = st.text_input("Email", placeholder="doctor@hospital.com or admin@system.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not email or not password:
                st.error("❌ Please fill in all fields")
                return
            
            if not validate_email(email):
                st.error("❌ Invalid email format. Use: user@example.com")
                return
            
            endpoint = "doctor" if user_type == "Doctor" else "admin"
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/auth/{endpoint}/login",
                    json={"email": email, "password": password}
                )
                
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
                st.error(f"❌ Connection error: {str(e)}")

def show_patient_registration():
    """Patient registration form with validation"""
    st.subheader("Register as New Patient")
    st.info("📋 Complete a health assessment to create your account")
    
    # Show validation rules
    with st.expander("📖 Registration Guidelines"):
        st.markdown("""
        **Email Format:** Must be valid (e.g., `patient@example.com`)
        - ✅ Good: `john@hospital.com`, `patient123@clinic.org`
        - ❌ Bad: `john@hospital`, `patient@123`
        
        **Password:** Minimum 6 characters
        
        **Phone:** At least 10 digits (e.g., `+1234567890` or `1234567890`)
        
        **Age:** Between 0-150 years
        """)
    
    with st.form("patient_registration_form"):
        st.markdown("#### Personal Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*", placeholder="John Doe")
            age = st.number_input("Age*", min_value=0, max_value=150, value=25)
            email = st.text_input("Email*", placeholder="patient@example.com", help="Must be valid email: user@example.com")
        
        with col2:
            gender = st.selectbox("Gender*", ["Male", "Female", "Other", "Prefer not to say"])
            phone = st.text_input("Phone*", placeholder="+1234567890", help="At least 10 digits")
            password = st.text_input("Password*", type="password", help="Minimum 6 characters")
        
        st.markdown("#### Health Information")
        
        symptom_name = st.text_input("Main Symptom Name*", placeholder="e.g., Headache, Fever, Cough", value="General Health Concern")
        symptoms_desc = st.text_area(
            "Describe your symptoms in detail*",
            placeholder="Please describe what you're experiencing...",
            height=150
        )
        
        st.markdown("#### Symptom Details (Optional)")
        col1, col2 = st.columns(2)
        with col1:
            duration = st.text_input("Duration", placeholder="e.g., 3 days")
            severity = st.text_input("Severity (1-10)", placeholder="e.g., 7")
        with col2:
            frequency = st.text_input("Frequency", placeholder="e.g., daily, hourly")
            factors = st.text_input("Triggering Factors", placeholder="e.g., after eating, morning")
        
        st.markdown("#### General Health Questions (Optional)")
        q1 = st.text_input("Do you have any chronic health conditions?", placeholder="e.g., Diabetes, Hypertension, or 'None'")
        q2 = st.text_input("Are you currently taking any medications?", placeholder="e.g., Aspirin, Insulin, or 'None'")
        q3 = st.text_input("Have you had any surgeries in the past?", placeholder="e.g., Appendectomy, or 'None'")
        q4 = st.text_input("Do you have any allergies?", placeholder="e.g., Penicillin, Pollen, or 'None'")
        q5 = st.text_input("How would you describe your overall health?", placeholder="e.g., Good, Fair, Poor")
        
        submit = st.form_submit_button("Complete Registration")
        
        if submit:
            # Validation
            if not all([name, age, email, phone, password, symptom_name, symptoms_desc]):
                st.error("❌ Please fill in all required fields marked with *")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be at least 6 characters long")
                return
            
            if not validate_email(email):
                st.error("❌ Invalid email format. Please use: user@example.com (must have @ and domain like .com)")
                return
            
            if not validate_phone(phone):
                st.error("❌ Phone number must contain at least 10 digits")
                return
            
            # Build patient data
            patient_data = {
                "demographic": {
                    "name": name,
                    "age": int(age),
                    "gender": gender,
                    "email": email,
                    "phone": phone
                },
                "per_symptom": {
                    symptom_name: {
                        "Duration": duration if duration else "Not specified",
                        "Severity": severity if severity else "Not specified",
                        "Frequency": frequency if frequency else "Not specified",
                        "Factors": factors if factors else "Not specified",
                        "Additional Notes": symptoms_desc
                    }
                },
                "Gen_questions": {
                    "Do you have any chronic health conditions?": q1 if q1 else "None",
                    "Are you currently taking any medications?": q2 if q2 else "None",
                    "Have you had any surgeries in the past?": q3 if q3 else "None",
                    "Do you have any allergies?": q4 if q4 else "None",
                    "How would you describe your overall health?": q5 if q5 else "Not specified"
                },
                "password": password
            }
            
            try:
                with st.spinner("Creating your account..."):
                    response = requests.post(
                        f"{API_BASE_URL}/api/auth/patient/register",
                        json=patient_data,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    st.success("✅ Registration successful! You are now logged in.")
                    st.balloons()
                    
                    # Auto-login
                    data = response.json()
                    st.session_state.logged_in = True
                    st.session_state.user_type = "patient"
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error(parse_api_error(response))
            except requests.exceptions.Timeout:
                st.error("❌ Request timeout. Please try again.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_staff_registration():
    """Doctor and Admin registration"""
    st.subheader("Staff Registration")
    
    reg_type = st.radio("Register as:", ["Doctor", "Admin"])
    
    if reg_type == "Doctor":
        show_doctor_registration()
    else:
        show_admin_registration()

def show_doctor_registration():
    """Doctor registration form with validation"""
    st.markdown("#### Register as New Doctor")
    st.info("📋 Your account will require admin approval before you can login")
    
    # Show validation rules
    with st.expander("📖 Registration Guidelines"):
        st.markdown("""
        **Email Format:** Must be valid (e.g., `doctor@hospital.com`)
        - ✅ Good: `dr.smith@hospital.com`, `doctor@clinic.org`
        - ❌ Bad: `doctor@123`, `doctor@hospital`
        
        **Password:** Minimum 6 characters
        
        **License Number:** Your medical license number (any format)
        """)
    
    with st.form("doctor_registration_form"):
        name = st.text_input("Full Name*", placeholder="Dr. John Smith")
        email = st.text_input("Email*", placeholder="doctor@hospital.com", help="Must be valid: user@example.com")
        specialization = st.text_input("Specialization*", placeholder="e.g., Cardiology, Pediatrics")
        license_number = st.text_input("Medical License Number*", placeholder="e.g., MD123456")
        password = st.text_input("Password*", type="password", help="Minimum 6 characters")
        password_confirm = st.text_input("Confirm Password*", type="password")
        
        submit = st.form_submit_button("Submit for Approval")
        
        if submit:
            if not all([name, email, specialization, license_number, password, password_confirm]):
                st.error("❌ Please fill in all required fields")
                return
            
            if password != password_confirm:
                st.error("❌ Passwords do not match")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be at least 6 characters long")
                return
            
            if not validate_email(email):
                st.error("❌ Invalid email format. Please use: user@example.com (must have @ and domain like .com)")
                return
            
            doctor_data = {
                "name": name,
                "email": email,
                "specialization": specialization,
                "license_number": license_number,
                "password": password
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/doctors/register",
                    json=doctor_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("✅ Doctor registration submitted!")
                    st.info("📧 Please wait for admin approval. You will be able to login once approved.")
                    st.balloons()
                else:
                    st.error(parse_api_error(response))
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_admin_registration():
    """Admin registration form with validation"""
    st.markdown("#### Create Admin Account")
    
    # Show validation rules
    with st.expander("📖 Registration Guidelines"):
        st.markdown("""
        **Email Format:** Must be valid (e.g., `admin@system.com`)
        - ✅ Good: `admin@hospital.com`, `admin@system.org`
        - ❌ Bad: `admin@123`, `admin@system`
        
        **Password:** Minimum 6 characters
        
        **Note:** This creates the first admin OR requires you to be logged in as admin
        """)
    
    with st.form("admin_registration_form"):
        st.warning("⚠️ This will create the first admin account OR requires you to be logged in as an admin")
        
        name = st.text_input("Full Name*", placeholder="Admin Name")
        email = st.text_input("Email*", placeholder="admin@system.com", help="Must be valid: user@example.com")
        password = st.text_input("Password*", type="password", help="Minimum 6 characters")
        password_confirm = st.text_input("Confirm Password*", type="password")
        
        submit = st.form_submit_button("Create Admin")
        
        if submit:
            if not all([name, email, password, password_confirm]):
                st.error("❌ Please fill in all required fields")
                return
            
            if password != password_confirm:
                st.error("❌ Passwords do not match")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be at least 6 characters long")
                return
            
            if not validate_email(email):
                st.error("❌ Invalid email format. Please use: user@example.com (must have @ and domain like .com)")
                return
            
            admin_data = {
                "name": name,
                "email": email,
                "password": password
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/admin/create-first",
                    json=admin_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("✅ First admin account created successfully!")
                    st.info("👉 You can now login using the 'Staff Login' tab")
                    st.balloons()
                else:
                    st.error(parse_api_error(response))
                    st.info("💡 If an admin already exists, please login as admin to create more admins")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_dashboard():
    """Show dashboard based on user type"""
    if st.session_state.user_type == "patient":
        show_patient_dashboard()
    elif st.session_state.user_type == "doctor":
        show_doctor_dashboard()
    elif st.session_state.user_type == "admin":
        show_admin_dashboard()

def show_patient_dashboard():
    """Patient dashboard"""
    st.title("👤 Patient Dashboard")
    
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/patients/me", headers=headers)
        if response.status_code == 200:
            patient_data = response.json()
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 My Profile", 
                "🩺 Health Records", 
                "✏️ Update Information",
                "💬 Chat Assistant"
            ])
            
            with tab1:
                st.subheader("Personal Information")
                demo = patient_data["demographic"]
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Name:** {demo['name']}")
                    st.info(f"**Age:** {demo['age']}")
                    st.info(f"**Gender:** {demo['gender']}")
                with col2:
                    st.info(f"**Email:** {demo['email']}")
                    st.info(f"**Phone:** {demo['phone']}")
            
            with tab2:
                st.subheader("Your Health Records")
                
                if patient_data.get("summary"):
                    st.markdown("#### Summary")
                    st.success(patient_data["summary"])
                
                st.markdown("#### Reported Symptoms")
                for symptom, details in patient_data["per_symptom"].items():
                    with st.expander(f"📌 {symptom.upper()}", expanded=True):
                        for key, value in details.items():
                            if value and value != "Not specified":
                                st.write(f"**{key}:** {value}")
                
                st.markdown("#### General Health Information")
                for question, answer in patient_data["gen_questions"].items():
                    st.write(f"**Q:** {question}")
                    st.write(f"**A:** {answer}")
                    st.markdown("---")
            
            with tab3:
                st.subheader("Update Your Information")
                st.info("🔄 Update your profile, symptoms, or health information")
                st.warning("⚠️ Update functionality - Contact your healthcare provider to update records")
            
            with tab4:
                st.subheader("Chat with Health Assistant")
                st.info("💬 Ask questions about your health assessment")
                
                user_message = st.text_input("Your message:")
                if st.button("Send"):
                    if user_message:
                        with st.spinner("Thinking..."):
                            chat_response = requests.post(
                                f"{API_BASE_URL}/api/patients/chat",
                                headers=headers,
                                json={"message": user_message, "conversation_history": []}
                            )
                            if chat_response.status_code == 200:
                                chat_data = chat_response.json()
                                st.success(f"🤖 Assistant: {chat_data['response']}")
                            else:
                                st.error("Failed to get response")
        else:
            st.error("Could not load patient data")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_doctor_dashboard():
    """Doctor dashboard - COMPLETE VERSION"""
    st.title("👨‍⚕️ Doctor Dashboard")
    
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    tab1, tab2, tab3 = st.tabs([
        "📊 All Patients",
        "🔍 Search Patient",
        "👤 Patient Details"
    ])
    
    with tab1:
        st.subheader("All Registered Patients")
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/patients/", headers=headers)
            if response.status_code == 200:
                patients = response.json()
                
                if not patients:
                    st.warning("No patients registered yet")
                else:
                    st.success(f"Total Patients: {len(patients)}")
                    
                    for idx, patient in enumerate(patients, 1):
                        with st.expander(f"{idx}. 👤 {patient['name']} - {patient.get('email', 'No email')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Age:** {patient.get('age', 'N/A')}")
                                st.write(f"**Patient ID:** {patient['id'][:8]}...")
                            with col2:
                                if st.button("View Full Record", key=f"view_{patient['id']}"):
                                    st.session_state.selected_patient_id = patient['id']
                                    st.rerun()
            else:
                st.error("Could not load patients")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Search for Patient")
        
        search_type = st.radio("Search by:", ["Name", "Email"])
        search_query = st.text_input(f"Enter patient {search_type.lower()}:")
        
        if st.button("Search"):
            if search_query:
                try:
                    response = requests.get(f"{API_BASE_URL}/api/patients/", headers=headers)
                    if response.status_code == 200:
                        patients = response.json()
                        
                        if search_type == "Name":
                            found = [p for p in patients if search_query.lower() in p['name'].lower()]
                        else:
                            found = [p for p in patients if search_query.lower() in p.get('email', '').lower()]
                        
                        if found:
                            st.success(f"Found {len(found)} patient(s)")
                            for patient in found:
                                with st.expander(f"👤 {patient['name']}"):
                                    st.write(f"**Email:** {patient.get('email')}")
                                    st.write(f"**Age:** {patient.get('age')}")
                                    if st.button("View Details", key=f"search_{patient['id']}"):
                                        st.session_state.selected_patient_id = patient['id']
                                        st.rerun()
                        else:
                            st.warning("No patients found matching your search")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab3:
        st.subheader("Patient Details")
        
        if 'selected_patient_id' in st.session_state:
            try:
                detail_response = requests.get(
                    f"{API_BASE_URL}/api/patients/{st.session_state.selected_patient_id}",
                    headers=headers
                )
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    
                    st.markdown("### 📋 Demographic Information")
                    demo = detail_data["demographic"]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Name:** {demo['name']}")
                        st.info(f"**Age:** {demo['age']}")
                        st.info(f"**Gender:** {demo['gender']}")
                    with col2:
                        st.info(f"**Email:** {demo['email']}")
                        st.info(f"**Phone:** {demo['phone']}")
                    
                    st.markdown("### 🩺 Symptoms and Health Data")
                    for symptom, details in detail_data["per_symptom"].items():
                        with st.expander(f"📌 {symptom.upper()}", expanded=True):
                            for key, value in details.items():
                                if value and value != "Not specified":
                                    st.write(f"**{key}:** {value}")
                    
                    st.markdown("### 📝 General Health Questionnaire")
                    for question, answer in detail_data["gen_questions"].items():
                        st.write(f"**Q:** {question}")
                        st.write(f"**A:** {answer}")
                        st.markdown("---")
                else:
                    st.error("Could not load patient details")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.info("👈 Select a patient from the 'All Patients' or 'Search Patient' tab")

def show_admin_dashboard():
    """Admin dashboard"""
    st.title("🔑 Admin Dashboard")
    
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    tab1, tab2, tab3 = st.tabs([
        "📊 Statistics",
        "👨‍⚕️ Manage Doctors",
        "➕ Add Admin"
    ])
    
    with tab1:
        st.subheader("System Statistics")
        try:
            patient_response = requests.get(f"{API_BASE_URL}/api/admin/patients/count", headers=headers)
            doctor_response = requests.get(f"{API_BASE_URL}/api/admin/doctors/count", headers=headers)
            
            if patient_response.status_code == 200 and doctor_response.status_code == 200:
                patient_count = patient_response.json()["count"]
                doctor_data = doctor_response.json()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Patients", patient_count)
                with col2:
                    st.metric("Approved Doctors", doctor_data["approved"])
                with col3:
                    st.metric("Pending Approvals", doctor_data["pending"])
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Doctor Management")
        st.info("Approve or reject pending doctor applications")
        # Add doctor management code here
    
    with tab3:
        st.subheader("Add New Administrator")
        with st.form("add_admin_form"):
            admin_name = st.text_input("Full Name*")
            admin_email = st.text_input("Email*")
            admin_password = st.text_input("Password*", type="password")
            
            submit = st.form_submit_button("Create Admin")
            
            if submit:
                if not validate_email(admin_email):
                    st.error("❌ Invalid email format")
                    return
                
                # Create admin logic here
                st.success("Admin created!")

if __name__ == "__main__":
    main()