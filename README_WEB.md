# 🏥 Medical Health Assessment System – Web Application

Python-based full-stack Medical Health Assessment System with FastAPI backend,
Streamlit frontend, MongoDB Atlas, and optional AI-powered symptom analysis.

====================================================
BADGES
====================================================

Python 3.10+
FastAPI
Streamlit
MongoDB Atlas

Live Demo: <YOUR DEPLOYED URL>

====================================================
WHAT’S NEW (WEB VERSION)
====================================================

• Converted from CLI to full-stack web application
• Streamlit frontend (no JavaScript required)
• FastAPI REST backend with JWT authentication
• Role-based access (Patient / Doctor / Admin)
• MongoDB Atlas cloud database
• Production-ready & cloud deployable
• Responsive UI (desktop + mobile)

====================================================
ARCHITECTURE OVERVIEW
====================================================

User Browser
    |
    | HTTPS
    v
Streamlit Frontend (Port 8501)
    |
    | REST API (JSON)
    v
FastAPI Backend (Port 8000)
    |
    | PyMongo
    v
MongoDB Atlas (Cloud)

Collections:
• patients  (AES-256 encrypted)
• doctors   (approval workflow)
• admins    (system control)

====================================================
QUICK START
====================================================

PREREQUISITES
• Python 3.10+
• Git
• MongoDB Atlas (free tier)

----------------------------------------------------
STEP 1: CLONE REPOSITORY
----------------------------------------------------

    git clone https://github.com/yourusername/IIS_Project_G13_Web.git
    cd IIS_Project_G13_Web

----------------------------------------------------
STEP 2: ENVIRONMENT VARIABLES
----------------------------------------------------

WINDOWS:
    copy .env.example .env
    notepad .env

LINUX / MAC:
    cp .env.example .env
    nano .env

Required variables:

    MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
    MONGODB_DB=health_chatbot_db
    SECRET_KEY=your-secret-key
    ENCRYPTION_KEY=your-encryption-key
    HUGGING_FACE_TOKEN=optional

----------------------------------------------------
STEP 3: CREATE VIRTUAL ENVIRONMENT
----------------------------------------------------

    python -m venv venv

----------------------------------------------------
STEP 4: ACTIVATE VIRTUAL ENVIRONMENT
----------------------------------------------------

WINDOWS (CMD):
    venv\Scripts\activate

WINDOWS (PowerShell):
    .\venv\Scripts\Activate.ps1

LINUX / MAC:
    source venv/bin/activate

----------------------------------------------------
STEP 5: INSTALL DEPENDENCIES
----------------------------------------------------

BACKEND:
    cd backend
    pip install -r requirements.txt
    cd ..

FRONTEND:
    cd frontend
    pip install -r requirements.txt
    cd ..

----------------------------------------------------
STEP 6: START APPLICATION
----------------------------------------------------

OPTION A (RECOMMENDED)

WINDOWS:
    start_dev.bat

LINUX / MAC:
    chmod +x start_dev.sh
    ./start_dev.sh

OPTION B (MANUAL)

Backend:
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Frontend:
    cd frontend
    streamlit run app.py

----------------------------------------------------
STEP 7: ACCESS APPLICATION
----------------------------------------------------

Frontend:  http://localhost:8501
Backend:   http://localhost:8000
API Docs:  http://localhost:8000/docs

====================================================
FEATURES
====================================================

PATIENT
• Register & login
• View encrypted health records
• Update profile
• Chat with AI assistant
• Multi-language support

DOCTOR
• Secure login
• View patient data (read-only)
• AI-assisted insights

ADMIN
• Approve doctors
• Manage users
• View system statistics

====================================================
SECURITY
====================================================

• JWT authentication
• Role-based authorization
• Password hashing (bcrypt)
• AES-256 data encryption
• HTTPS-ready
• CORS protection
• Input validation via Pydantic

====================================================
API ENDPOINTS
====================================================

AUTH
• POST /api/auth/patient/register
• POST /api/auth/patient/login
• POST /api/auth/doctor/login
• POST /api/auth/admin/login

PATIENT
• GET  /api/patients/me
• PUT  /api/patients/me
• POST /api/patients/analyze-symptoms
• POST /api/patients/chat

DOCTOR
• GET /api/patients
• GET /api/patients/{id}
• POST /api/doctors/register

ADMIN
• POST /api/admin/create
• GET  /api/admin/doctors/pending
• POST /api/admin/doctors/approve

SYSTEM
• GET /
• GET /health

====================================================
PROJECT STRUCTURE
====================================================

IIS_Project_G13_Web/
│
├── backend/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── models/
│   └── requirements.txt
│
├── frontend/
│   ├── app.py
│   ├── pages/
│   └── requirements.txt
│
├── shared/
│   └── knowledge_base.json
│
├── .env.example
├── start_dev.bat
├── start_dev.sh
├── DEPLOYMENT_GUIDE.md
└── README_WEB.md

====================================================
DEPLOYMENT
====================================================

OPTION 1: RENDER + STREAMLIT CLOUD
• Backend → Render Web Service
• Frontend → Streamlit Cloud

OPTION 2: DOCKER
    docker-compose up -d

OPTION 3: AWS EC2
• Ubuntu 22.04
• Use systemd + Nginx

(See DEPLOYMENT_GUIDE.md for full steps)

====================================================
TROUBLESHOOTING
====================================================

WINDOWS PORT ISSUE:
    netstat -ano | findstr :8000
    taskkill /PID <PID> /F

LINUX / MAC PORT ISSUE:
    lsof -i :8000
    kill -9 <PID>

MONGODB TEST:
    python -c "from pymongo import MongoClient; MongoClient('URI').server_info()"

====================================================
ROADMAP
====================================================

• Email verification
• Password reset
• 2FA
• PDF reports
• Appointment scheduling
• Video consultations
• Mobile app

====================================================
LICENSE
====================================================

MIT License

====================================================
SUPPORT
====================================================

GitHub Issues
API Docs: /docs

====================================================
END
====================================================
