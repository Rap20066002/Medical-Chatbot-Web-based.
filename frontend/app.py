"""
Streamlit Frontend - Main Application (FIXED VERSION)
Medical Health Assessment Chatbot UI
"""

import streamlit as st
import requests
from datetime import datetime
import os

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
    tab1, tab2, tab3 = st.tabs(["👤 Patient Login", "👨‍⚕️ Doctor/Admin Login", "📝 Register"])
    
    with tab1:
        show_patient_login()
    
    with tab2:
        show_staff_login()
    
    with tab3:
        show_registration()

def show_patient_login():
    """Patient login form"""
    st.subheader("Patient Login")
    
    with st.form("patient_login_form"):
        email = st.text_input("Email", placeholder="patient@example.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not email or not password:
                st.error("Please fill in all fields")
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
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Login failed"))
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_staff_login():
    """Doctor/Admin login form"""
    st.subheader("Doctor & Admin Login")
    
    user_type = st.radio("Select user type:", ["Doctor", "Admin"])
    
    with st.form("staff_login_form"):
        email = st.text_input("Email", placeholder="doctor@hospital.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not email or not password:
                st.error("Please fill in all fields")
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
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Login failed"))
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_registration():
    """Patient registration form - FIXED VERSION"""
    st.subheader("Register as New Patient")
    st.info("Complete a health assessment to create your account")
    
    with st.form("registration_form"):
        st.markdown("#### Personal Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*", placeholder="John Doe")
            age = st.number_input("Age*", min_value=0, max_value=150, value=25)
            email = st.text_input("Email*", placeholder="patient@example.com")
        
        with col2:
            gender = st.selectbox("Gender*", ["Male", "Female", "Other", "Prefer not to say"])
            phone = st.text_input("Phone*", placeholder="+1234567890")
            password = st.text_input("Password* (min 6 characters)", type="password", help="Must be at least 6 characters")
        
        st.markdown("#### Health Information")
        symptoms = st.text_area(
            "Describe your symptoms*",
            placeholder="Please describe what you're experiencing...",
            height=150
        )
        
        st.markdown("#### General Health Questions")
        q1 = st.text_input("Do you have any chronic health conditions?", placeholder="None" if not st.session_state.get('q1') else "")
        q2 = st.text_input("Are you currently taking any medications?", placeholder="None" if not st.session_state.get('q2') else "")
        q3 = st.text_input("Do you have any allergies?", placeholder="None" if not st.session_state.get('q3') else "")
        
        submit = st.form_submit_button("Complete Registration")
        
        if submit:
            # Validation
            if not all([name, age, email, phone, password, symptoms]):
                st.error("❌ Please fill in all required fields marked with *")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be at least 6 characters long")
                return
            
            if '@' not in email or '.' not in email:
                st.error("❌ Please enter a valid email address (e.g., user@example.com)")
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
                    "general": {
                        "Duration": "Not specified",
                        "Severity": "Not specified",
                        "Frequency": "Not specified",
                        "Additional Notes": symptoms
                    }
                },
                "Gen_questions": {
                    "Chronic conditions": q1 if q1 else "None",
                    "Medications": q2 if q2 else "None",
                    "Allergies": q3 if q3 else "None"
                },
                "password": password
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/auth/patient/register",
                    json=patient_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("✅ Registration successful! You can now login.")
                    st.balloons()
                    st.info("👉 Go to the 'Patient Login' tab to sign in")
                else:
                    error_detail = response.json().get("detail", "Registration failed")
                    st.error(f"❌ {error_detail}")
            except requests.exceptions.Timeout:
                st.error("❌ Request timeout. Please try again.")
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
    
    # Get patient data
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/patients/me", headers=headers)
        if response.status_code == 200:
            patient_data = response.json()
            
            tab1, tab2, tab3 = st.tabs(["📋 My Profile", "🩺 Health Records", "💬 Chat Assistant"])
            
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
                
                st.markdown("#### Symptoms")
                for symptom, details in patient_data["per_symptom"].items():
                    with st.expander(f"📌 {symptom.upper()}"):
                        for key, value in details.items():
                            if value:  # Only show non-empty values
                                st.write(f"**{key}:** {value}")
                
                st.markdown("#### General Health Information")
                for question, answer in patient_data["gen_questions"].items():
                    st.write(f"**Q:** {question}")
                    st.write(f"**A:** {answer}")
                    st.markdown("---")
            
            with tab3:
                st.subheader("Chat with Health Assistant")
                st.info("💬 Ask questions about your health assessment")
                
                user_message = st.text_input("Your message:")
                if st.button("Send"):
                    if user_message:
                        with st.spinner("Thinking..."):
                            response = requests.post(
                                f"{API_BASE_URL}/api/patients/chat",
                                headers=headers,
                                json={"message": user_message, "conversation_history": []}
                            )
                            if response.status_code == 200:
                                chat_data = response.json()
                                st.success(f"🤖 Assistant: {chat_data['response']}")
                            else:
                                st.error("Failed to get response")
        else:
            st.error("Could not load patient data")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_doctor_dashboard():
    """Doctor dashboard"""
    st.title("👨‍⚕️ Doctor Dashboard")
    st.info("View and manage patient records")
    
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/patients/", headers=headers)
        if response.status_code == 200:
            patients = response.json()
            
            st.subheader(f"📊 All Patients ({len(patients)})")
            
            if not patients:
                st.warning("No patients registered yet")
                return
            
            for patient in patients:
                with st.expander(f"👤 {patient['name']} - {patient.get('email', 'No email')}"):
                    st.write(f"**Age:** {patient.get('age', 'N/A')}")
                    st.write(f"**Patient ID:** {patient['id']}")
                    
                    if st.button(f"View Full Record", key=patient['id']):
                        # Fetch full patient details
                        detail_response = requests.get(
                            f"{API_BASE_URL}/api/patients/{patient['id']}",
                            headers=headers
                        )
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            
                            st.markdown("### Patient Details")
                            st.json(detail_data)
                        else:
                            st.error("Could not load patient details")
        else:
            st.error("Could not load patients")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_admin_dashboard():
    """Admin dashboard"""
    st.title("🔑 Admin Dashboard")
    
    st.markdown("### System Administration")
    
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    tab1, tab2, tab3 = st.tabs(["📊 Statistics", "👨‍⚕️ Doctor Approvals", "⚙️ Settings"])
    
    with tab1:
        st.subheader("System Statistics")
        
        try:
            # Get patient count
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
            else:
                st.error("Could not load statistics")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Pending Doctor Approvals")
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/admin/doctors/pending", headers=headers)
            if response.status_code == 200:
                pending_doctors = response.json()
                
                if not pending_doctors:
                    st.info("✅ No pending doctor approvals")
                else:
                    for doctor in pending_doctors:
                        with st.expander(f"Dr. {doctor['name']} - {doctor['specialization']}"):
                            st.write(f"**Email:** {doctor['email']}")
                            st.write(f"**License:** {doctor['license_number']}")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("✅ Approve", key=f"approve_{doctor['id']}"):
                                    approve_response = requests.post(
                                        f"{API_BASE_URL}/api/admin/doctors/approve",
                                        headers=headers,
                                        json={"doctor_id": doctor['id'], "approved": True}
                                    )
                                    if approve_response.status_code == 200:
                                        st.success("Doctor approved!")
                                        st.rerun()
                                    else:
                                        st.error("Approval failed")
                            
                            with col2:
                                if st.button("❌ Reject", key=f"reject_{doctor['id']}"):
                                    reject_response = requests.post(
                                        f"{API_BASE_URL}/api/admin/doctors/approve",
                                        headers=headers,
                                        json={"doctor_id": doctor['id'], "approved": False}
                                    )
                                    if reject_response.status_code == 200:
                                        st.success("Doctor rejected!")
                                        st.rerun()
                                    else:
                                        st.error("Rejection failed")
            else:
                st.error("Could not load pending doctors")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab3:
        st.subheader("System Settings")
        st.info("⚙️ Settings panel coming soon!")

if __name__ == "__main__":
    main()