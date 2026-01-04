# 🏥 Medical Health Assessment System

AI-powered healthcare assessment system with multilingual support, built with FastAPI, Streamlit, and MongoDB.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)

**🌐 Live Demo:** https://healthcare-frontend.streamlit.app

**📚 API Documentation:** https://healthcare-backend-vyzm.onrender.com/docs

---

## ✨ Key Features

- 🤖 **AI-Powered Symptom Analysis** - Mistral-7B LLM integration for intelligent clinical insights
- 🌍 **Multilingual Support** - Supports 30+ languages with automatic detection and translation
- 🔒 **Enterprise Security** - AES-256 encryption + JWT authentication for all sensitive data
- 👥 **Role-Based Access** - Separate dashboards for Patients, Doctors, and Administrators
- 📄 **PDF Reports** - Generate comprehensive health assessment reports with full Unicode support
- 🔄 **Real-Time Analysis** - Instant symptom detection with AI-generated follow-up questions
- 🩺 **Clinical Insights** - AI-powered differential diagnoses and red flag detection for doctors

---

## 🎯 What This System Does

This healthcare assessment system allows patients to describe their symptoms in natural language (in any of 30+ supported languages), and the AI automatically:

1. **Detects symptoms** from free-text descriptions
2. **Extracts details** (duration, severity, frequency, triggers)
3. **Generates follow-up questions** to gather missing information
4. **Creates clinical summaries** for doctor review
5. **Provides differential diagnoses** and recommended investigations
6. **Generates PDF reports** that patients and doctors can download

All patient data is encrypted at rest using AES-256, and the system uses JWT tokens for stateless authentication.

---

## 🏗️ System Architecture
```
User Browser
    ↓ HTTPS
Streamlit Frontend (https://healthcare-frontend.streamlit.app)
    ↓ REST API (JSON)
FastAPI Backend (https://healthcare-backend-vyzm.onrender.com)
    ↓ Encrypted Storage
MongoDB Atlas (Cloud Database)
```

**Technology Stack:**

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit 1.29+ | Interactive web UI with session management |
| **Backend** | FastAPI 0.104+ | High-performance REST API with async support |
| **Database** | MongoDB Atlas | Cloud-hosted NoSQL database with field-level encryption |
| **Authentication** | JWT + Bcrypt | Stateless token-based auth with hashed passwords |
| **AI/ML** | Mistral-7B LLM | Clinical summary generation and symptom analysis |
| **Translation** | Google Translate API | Real-time language detection and translation |
| **Encryption** | Cryptography (Fernet) | AES-256 encryption for all patient data |
| **PDF Generation** | ReportLab + Noto Fonts | Multilingual PDF reports with proper Unicode rendering |

---

## 🚀 Live Demo Access

### For Patients:
1. Visit: https://healthcare-frontend.streamlit.app
2. Click **"Patient Registration"** tab
3. Describe your symptoms in any language
4. AI will analyze and ask follow-up questions
5. Complete registration to access your dashboard

### For Doctors:
1. Register as doctor (requires admin approval)
2. Admin must approve your account
3. Login to view all patient records
4. Generate AI-powered clinical insights

### For Testing:
You can create an admin account if none exists, then approve doctor registrations.

---

## 🔐 Security Features

This system implements enterprise-grade security:

- ✅ **AES-256 Encryption** - All patient demographic data, symptoms, and health information encrypted at rest
- ✅ **JWT Authentication** - Stateless token-based authentication with 24-hour expiration
- ✅ **Bcrypt Password Hashing** - Industry-standard password security with automatic salting
- ✅ **Role-Based Authorization** - Granular access control (Patient/Doctor/Admin roles)
- ✅ **CORS Protection** - Configured to allow only authorized frontend domains
- ✅ **Input Validation** - Pydantic models with strict type checking on all API endpoints
- ✅ **HTTPS/TLS 1.3** - End-to-end encryption for all data in transit

**Example:** Even if someone gains database access, all patient data appears as encrypted strings:
```
"name": "gAAAAABh4K8L..." (encrypted)
"symptoms": "gAAAAABh4K9M..." (encrypted)
```

---

## 📊 System Capabilities

### 👤 For Patients

- **Register with Natural Language**: Describe symptoms conversationally
  - Example: *"I've had severe headache for a week, 8/10 pain, every morning"*
- **AI Symptom Analysis**: System automatically detects symptoms and asks targeted questions
- **Multilingual Interface**: Type in any of 30+ languages - system auto-detects
- **Secure Dashboard**: View personal health records
- **PDF Reports**: Download comprehensive health assessment reports
- **Update Records**: Modify symptoms, demographics, or health information anytime
- **Password Management**: Change password securely

### 👨‍⚕️ For Doctors

- **Patient Overview**: View all registered patients with search functionality
- **Detailed Records**: Access complete patient histories with symptom timelines
- **AI Clinical Insights**: Generate differential diagnoses and red flag alerts
  - Recommended investigations
  - Clinical significance assessment
  - Warning signs to monitor
- **PDF Downloads**: Download patient reports for offline review
- **Search & Filter**: Find patients by name or email
- **Secure Access**: All actions logged and authenticated

### 🔑 For Administrators

- **Doctor Approval Workflow**: Review and approve/reject doctor registrations
- **User Management**: View all patients and doctors in the system
- **Account Control**: Enable/disable doctor accounts
- **System Statistics**: Monitor total users and pending approvals
- **Admin Creation**: Create additional administrators
- **Audit Trail**: Track all approval actions

---

## 🌐 Supported Languages

The system supports **30+ languages** with automatic detection and translation:

**Latin Script:** English, Spanish, French, German, Italian, Portuguese, Dutch, Swedish, Polish, Turkish

**Cyrillic:** Russian, Ukrainian, Bulgarian

**Arabic Script:** Arabic, Persian, Urdu

**Indic Scripts:** Hindi, Bengali, Tamil, Telugu, Marathi, **Gujarati**

**East Asian:** Chinese (Simplified & Traditional), Japanese, Korean

**Southeast Asian:** Thai, Vietnamese

**Other:** Hebrew, Greek

**How it works:**
1. Patient types in their native language
2. System detects language automatically
3. Offers to switch interface to that language
4. All UI elements translate dynamically
5. PDF reports support all scripts with proper fonts

---

## 📁 Project Structure
```
healthcare-assessment-system/
│
├── backend/                    # FastAPI REST API
│   ├── api/
│   │   ├── middleware/
│   │   │   └── auth.py        # JWT authentication middleware
│   │   └── routes/
│   │       ├── auth.py        # Login/registration endpoints
│   │       ├── patients.py    # Patient management
│   │       ├── doctors.py     # Doctor management
│   │       ├── admin.py       # Admin operations
│   │       └── language.py    # Translation services
│   ├── core/
│   │   ├── config.py          # Environment configuration
│   │   ├── database.py        # MongoDB connection + encryption
│   │   └── llm.py             # AI/LLM integration
│   ├── models/
│   │   └── patient.py         # Pydantic data models
│   ├── utils/
│   │   └── pdf_generator.py  # Multilingual PDF generation
│   ├── main.py                # FastAPI application entry point
│   └── requirements.txt
│
├── frontend/                   # Streamlit Web UI
│   ├── app.py                 # Main Streamlit application
│   └── requirements.txt
│
├── shared/
│   └── knowledge_base.json    # Medical symptoms database (232 symptoms)
│
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── DEPLOYMENT_GUIDE.md        # Step-by-step deployment instructions
├── INTERVIEW_PREP_WEB.md      # Technical interview preparation guide
└── start_dev.bat              # Windows development startup script
```

---

## 🔧 Local Development Setup

Want to run this locally? Follow these steps:

### Prerequisites
- Python 3.10 or higher
- MongoDB Atlas account (free tier available)
- Git installed

### Step 1: Clone Repository
```bash
git clone https://github.com/Rap20066002/Medical-Chatbot-Web-based..git
cd Medical-Chatbot-Web-based.
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
pip install -r requirements.txt
cd ..
```

### Step 4: Configure Environment
```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your actual values
notepad .env
```

Required environment variables:
```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB=health_chatbot_db
SECRET_KEY=your-secret-key-min-32-characters
ENCRYPTION_KEY=your-fernet-encryption-key
HUGGING_FACE_TOKEN=your_huggingface_token_here
USE_LLM=False
FRONTEND_URL=http://localhost:8501
DEBUG=True
```

**Generate encryption key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 5: Run Application

**Option A: Using startup script (Windows):**
```bash
start_dev.bat
```

**Option B: Manual start:**

Terminal 1 (Backend):
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
streamlit run app.py
```

### Step 6: Access Application

- **Frontend UI:** http://localhost:8501
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

---

## 🧪 API Endpoints Reference

### Authentication Endpoints
```http
POST /api/auth/patient/register
POST /api/auth/patient/login
POST /api/auth/doctor/login
POST /api/auth/admin/login
```

### Patient Endpoints (Requires Patient Auth)
```http
GET  /api/patients/me                      # Get current patient profile
PUT  /api/patients/me                      # Update patient information
POST /api/patients/analyze-symptoms        # Analyze symptom description
GET  /api/patients/me/pdf                  # Download health report PDF
POST /api/patients/me/change-password      # Change password
POST /api/patients/me/regenerate-summary   # Regenerate clinical summary
```

### Doctor Endpoints (Requires Doctor Auth)
```http
POST /api/doctors/register                           # Register new doctor
GET  /api/doctors/me                                 # Get doctor profile
POST /api/doctors/change-password                    # Change password
GET  /api/patients/                                  # List all patients
GET  /api/patients/{id}                             # Get patient details
GET  /api/patients/{id}/pdf                         # Download patient PDF
POST /api/patients/{id}/clinical-insights           # Generate AI insights
GET  /api/patients/{id}/clinical-insights           # Get insights status
```

### Admin Endpoints (Requires Admin Auth)
```http
POST /api/admin/create-first                # Create first admin (no auth required)
POST /api/admin/create                      # Create additional admin
POST /api/admin/change-password             # Change admin password
GET  /api/admin/doctors/pending             # Get pending doctor approvals
GET  /api/admin/doctors/all                 # Get all doctors
POST /api/admin/doctors/approve             # Approve/reject doctor
POST /api/admin/doctors/toggle              # Enable/disable doctor account
GET  /api/admin/patients/count              # Get patient statistics
GET  /api/admin/patients/all                # Get all patients (demographics only)
GET  /api/admin/doctors/count               # Get doctor statistics
```

### Language Endpoints
```http
POST /api/language/detect                   # Detect language from text
POST /api/language/translate                # Translate text
GET  /api/language/supported                # Get supported languages list
```

### System Endpoints
```http
GET  /                                      # API information
GET  /health                                # Health check
```

**Full Interactive Documentation:** https://healthcare-backend-vyzm.onrender.com/docs

---

## 💡 Key Implementation Details

### AI-Powered Symptom Analysis

The system uses a multi-step approach:

1. **Language Detection**: Automatically detects input language
2. **Translation**: Translates to English for processing (if needed)
3. **LLM Processing**: Uses Mistral-7B to:
   - Extract medical symptoms from natural language
   - Identify severity, duration, frequency, and triggers
   - Generate targeted follow-up questions
4. **Template Fallback**: If LLM unavailable, uses template-based summaries

**Example Flow:**
```
Input (Gujarati): "મને ખૂબ તાવ છે, માથાનો દુખાવો..."
    ↓ Detect Language
Language: Gujarati (high confidence)
    ↓ Translate
English: "I have high fever, severe headache..."
    ↓ LLM Analysis
Symptoms: ["fever", "headache", "stiff neck", "sensitivity to light"]
Details: {Severity: "Severe", Duration: "3 days"}
    ↓ Generate Questions
1. How long have you had the fever?
2. Rate headache severity 1-10?
```

### Encryption Implementation

**Field-Level Encryption:**
```python
# Before storage:
patient_data = {
    "name": "John Doe",
    "symptoms": "headache"
}

# After encryption:
encrypted_data = {
    "name": "gAAAAABh4K8L7n...",  # AES-256 encrypted
    "symptoms": "gAAAAABh4K9Mx..."
}
```

**Decryption happens only:**
- When patient views their own data
- When doctor with valid JWT accesses patient
- When admin views patient demographics

### JWT Authentication Flow
```
1. User logs in → Server verifies credentials
2. Server generates JWT:
   {
     "sub": "user@email.com",
     "user_type": "patient",
     "exp": 1735689600  // 24 hours from now
   }
3. Client stores token
4. All requests include: Authorization: Bearer <token>
5. Server verifies token signature and expiration
6. Grants access based on user_type
```

---

## 🎯 Deployment Configuration

### Production Environment Variables

**Backend (Render.com):**
```env
USE_LLM=False                              # Template-based summaries (instant)
DEBUG=False                                # Disable debug mode
MONGODB_URI=mongodb+srv://...              # Atlas connection string
SECRET_KEY=<strong-random-key>             # 32+ character secret
ENCRYPTION_KEY=<fernet-key>                # Generated Fernet key
HUGGING_FACE_TOKEN=your_huggingface_token_here
FRONTEND_URL=https://healthcare-frontend.streamlit.app
```

**Frontend (Streamlit Cloud):**
```toml
# Secrets (TOML format)
API_BASE_URL = "https://healthcare-backend-vyzm.onrender.com"
```

### Why LLM is Disabled in Production

The deployed version uses `USE_LLM=False` for optimal performance:

- ✅ **Instant response times** (no 5-10 minute wait)
- ✅ **No GPU required** (free tier deployment)
- ✅ **Template-based summaries** work perfectly for demonstration
- ✅ **All other features fully functional**

**Note:** The codebase fully supports LLM mode (Mistral-7B). To enable locally:
1. Set `USE_LLM=True` in `.env`
2. Provide `HUGGING_FACE_TOKEN`
3. Have at least 8GB RAM
4. Expect 5-10 minute processing time per patient registration

---

## 📊 Performance Characteristics

### Response Times (Production)

| Operation | Time | Notes |
|-----------|------|-------|
| Patient Registration | 2-5 seconds | Without LLM (template summaries) |
| Symptom Analysis | 1-2 seconds | Language detection + translation |
| PDF Generation | 3-5 seconds | Full multilingual report |
| Clinical Insights | Instant | Template-based (LLM: 5-10 min) |
| Login/Auth | < 1 second | JWT token generation |

### Scalability Considerations

- **Stateless API**: Horizontally scalable (add more servers)
- **MongoDB Atlas**: Auto-scales with load
- **JWT Authentication**: No session storage needed
- **Free Tier Limitation**: Backend sleeps after 15 min inactivity (30-60s cold start)

---

## 🐛 Known Limitations

1. **Free Tier Sleep**: Backend on Render free tier sleeps after inactivity - first request may take 30-60 seconds
2. **Translation Rate Limits**: Google Translate API has rate limits - may fail under very heavy load
3. **LLM Disabled**: Production uses template summaries for performance (LLM available in code)
4. **PDF Font Coverage**: Some rare Unicode characters may not render perfectly

**Future Improvements:**
- Implement Redis caching for translations
- Add rate limiting middleware
- Upgrade to paid tier for always-on backend
- Add email notifications for doctor approvals

---

## 📚 Additional Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment walkthrough from scratch
- **[INTERVIEW_PREP_WEB.md](INTERVIEW_PREP_WEB.md)** - Technical interview preparation guide with Q&A
- **[API Documentation](https://healthcare-backend-vyzm.onrender.com/docs)** - Interactive Swagger UI

---

## 🎓 Project Background

**Course:** Information and Intelligence Systems (IIS) - Course Project  
**Institution:** Indraprastha Institute of Information Technology Delhi (IIIT-D)  
**Year:** 2nd Year (2024-2025)  
**Duration:** 2 weeks development + 4 months course project timeline  
**Team Size:** 6

**Learning Outcomes:**
- Full-stack web application development
- RESTful API design and implementation
- Database design with encryption
- AI/ML integration (LLM)
- Cloud deployment (Render, Streamlit Cloud, MongoDB Atlas)
- Security best practices (JWT, AES-256, Bcrypt)
- Multilingual application development

---

## 🤝 Contributing

This is an academic course project.

---

## 👨‍💻 Developer

**Punjani Rezaabbas Alihasnain**

- 🎓 2nd Year, IIIT Delhi
- 📧 Email: [rezaabbaspunjani28@gmail.com](mailto:rezaabbaspunjani28@gmail.com)
- 💼 LinkedIn: [linkedin.com/in/reza-abbas-punjani-b44412312](https://www.linkedin.com/in/reza-abbas-punjani-b44412312)
- 💻 GitHub: [@Rap20066002](https://github.com/Rap20066002)

---

## 🙏 Acknowledgments

- **Mistral AI** for the Mistral-7B language model
- **MongoDB Atlas** for cloud database hosting
- **Render.com** and **Streamlit Cloud** for deployment platforms
- **Google Translate API** for multilingual support
- **FastAPI** and **Streamlit** communities for excellent documentation

---

## 📞 Support & Feedback

**Found a bug?** Open an issue on GitHub  
**Have questions?** Email me at rezaabbaspunjani28@gmail.com  
**Want to collaborate?** Connect on LinkedIn

---

<div align="center">

**⭐ Star this repository if you found it helpful!**

**🌐 Live Demo:** https://healthcare-frontend.streamlit.app

**Built with ❤️ using FastAPI, Streamlit, and MongoDB**

---

*Last Updated: January 2025*

</div>