# 🏥 Medical Health Assessment System – Web Application

Python-based full-stack Medical Health Assessment System with FastAPI backend, Streamlit frontend, MongoDB Atlas, and optional AI-powered symptom analysis.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)

**Live Demo:** [Your Deployed URL]

---

## 📋 Table of Contents

- [What's New](#whats-new)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Field Constraints & Validation](#field-constraints--validation)
- [Features](#features)
- [Security](#security)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

---

## 🆕 What's New (Web Version)

- ✅ Converted from CLI to full-stack web application
- ✅ Streamlit frontend (no JavaScript required)
- ✅ FastAPI REST backend with JWT authentication
- ✅ Role-based access (Patient / Doctor / Admin)
- ✅ MongoDB Atlas cloud database
- ✅ Production-ready & cloud deployable
- ✅ Responsive UI (desktop + mobile)
- ✅ User-friendly error messages
- ✅ Client-side validation

---

## 🏗️ Architecture Overview

```
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
```

**Collections:**
- `patients` (AES-256 encrypted)
- `doctors` (approval workflow)
- `admins` (system control)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Git
- MongoDB Atlas account (free tier)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/IIS_Project_G13_Web.git
cd IIS_Project_G13_Web
```

### Step 2: Environment Variables

**Windows:**
```cmd
copy .env.example .env
notepad .env
```

**Linux/Mac:**
```bash
cp .env.example .env
nano .env
```

**Required variables:**
```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB=health_chatbot_db
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
HUGGING_FACE_TOKEN=optional
```

### Step 3: Virtual Environment

```bash
python -m venv venv
```

**Activate:**
- Windows CMD: `venv\Scripts\activate`
- Windows PowerShell: `.\venv\Scripts\Activate.ps1`
- Linux/Mac: `source venv/bin/activate`

### Step 4: Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
pip install -r requirements.txt
cd ..
```

### Step 5: Start Application

**Option A (Recommended) - Using Scripts:**

Windows:
```cmd
start_dev.bat
```

Linux/Mac:
```bash
chmod +x start_dev.sh
./start_dev.sh
```

**Option B - Manual:**

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
streamlit run app.py
```

### Step 6: Access Application

- **Frontend:** http://localhost:8501
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 📝 Field Constraints & Validation

### Email Format (All Users)

**Required Format:** `username@domain.extension`

✅ **Valid Examples:**
```
patient@example.com
john.doe@hospital.org
doctor123@clinic.co.uk
admin@health-system.com
```

❌ **Invalid Examples:**
```
patient@123          # Missing domain extension
doctor@hospital      # Missing .com, .org, etc.
admin@               # Missing domain
@example.com         # Missing username
patient.com          # Missing @ symbol
```

**Validation Rules:**
- Must contain exactly one `@` symbol
- Must have username before `@`
- Must have domain after `@` with at least one period (.)
- Domain extension must be 2+ characters (e.g., `.com`, `.org`, `.co.uk`)
- Automatically converted to lowercase

---

### Password Requirements (All Users)

**Minimum Length:** 6 characters

✅ **Valid Examples:**
```
password123
MyPass123!
secure@2024
```

❌ **Invalid Examples:**
```
pass        # Too short (< 6 characters)
12345       # Too short
abc         # Too short
```

**Best Practices:**
- Use mix of uppercase, lowercase, numbers, symbols
- Avoid common words like "password", "123456"
- Don't use personal information

---

### Phone Number (Patients)

**Minimum:** 10 digits (any format)

✅ **Valid Examples:**
```
+1234567890
1234567890
(123) 456-7890
+91-9876543210
123-456-7890
```

❌ **Invalid Examples:**
```
123456789       # Only 9 digits
12345           # Too short
abc1234567      # Contains letters
```

**Validation:**
- Strips all non-digit characters
- Checks if remaining digits >= 10
- Accepts international formats

---

### Age (Patients)

**Range:** 0 - 150 years

✅ **Valid:** Any integer from 0 to 150

❌ **Invalid:**
```
-5          # Negative
151         # Above maximum
abc         # Non-numeric
25.5        # Decimal (must be integer)
```

---

### Name Fields (All Users)

**Minimum Length:** 2 characters
**Maximum Length:** 100 characters

✅ **Valid Examples:**
```
John Doe
Dr. Sarah Smith
Admin User
```

❌ **Invalid Examples:**
```
J           # Too short (< 2 chars)
[Empty]     # Required field
```

---

### Medical License Number (Doctors)

**Format:** Any alphanumeric string

✅ **Valid Examples:**
```
MD123456
DOC-2024-001
LICENSE789
```

**Required:** Must not be empty

---

### Specialization (Doctors)

**Format:** Free text

✅ **Valid Examples:**
```
Cardiology
General Surgery
Pediatrics
Internal Medicine
```

**Required:** Must not be empty

---

## 🎯 Registration Guidelines

### Patient Registration

**Required Fields (marked with *):**
1. Full Name
2. Age
3. Email (valid format)
4. Gender
5. Phone (10+ digits)
6. Password (6+ characters)
7. Main Symptom Name
8. Symptom Description

**Optional Fields:**
- Duration, Severity, Frequency, Factors
- General health questions

**Steps:**
1. Click "Patient Registration" tab
2. Fill personal information
3. Describe your symptoms
4. Answer health questions (optional)
5. Click "Complete Registration"

---

### Doctor Registration

**Required Fields:**
1. Full Name
2. Email (valid format)
3. Specialization
4. Medical License Number
5. Password (6+ characters)
6. Confirm Password (must match)

**Process:**
1. Submit registration form
2. Wait for admin approval
3. Receive email notification (if configured)
4. Login once approved

---

### Admin Registration

**First Admin:**
- Can be created if no admin exists
- Requires all fields

**Additional Admins:**
- Must be created by existing admin
- Same field requirements

---

## ✨ Features

### For Patients
- ✅ Register & login
- ✅ View encrypted health records
- ✅ Update profile
- ✅ Chat with AI assistant
- ✅ Multi-language support

### For Doctors
- ✅ Secure login
- ✅ View all patients
- ✅ Search patients by name/email
- ✅ View detailed patient records
- ✅ AI-assisted insights

### For Admins
- ✅ Approve/reject doctors
- ✅ Manage user accounts
- ✅ View system statistics
- ✅ Create new admins

---

## 🔒 Security

- **JWT Authentication:** Stateless token-based auth
- **Role-Based Authorization:** Patient/Doctor/Admin roles
- **Password Hashing:** Bcrypt with auto-salting
- **AES-256 Encryption:** All patient data encrypted
- **HTTPS Ready:** TLS 1.3 support
- **CORS Protection:** Configurable origins
- **Input Validation:** Pydantic models

---

## 📡 API Endpoints

### Authentication
```
POST /api/auth/patient/register     # Patient registration
POST /api/auth/patient/login        # Patient login
POST /api/auth/doctor/login         # Doctor login
POST /api/auth/admin/login          # Admin login
```

### Patients
```
GET  /api/patients/me               # Get current patient
PUT  /api/patients/me               # Update patient
POST /api/patients/analyze-symptoms # Analyze symptoms
POST /api/patients/chat             # Chat with AI
GET  /api/patients/{id}             # Get patient by ID (doctors)
GET  /api/patients/                 # List all patients (doctors)
```

### Doctors
```
POST /api/doctors/register          # Doctor registration
```

### Admin
```
POST /api/admin/create              # Create admin
POST /api/admin/create-first        # Create first admin
GET  /api/admin/doctors/pending     # Pending approvals
POST /api/admin/doctors/approve     # Approve/reject doctor
GET  /api/admin/patients/count      # Patient count
GET  /api/admin/doctors/count       # Doctor statistics
```

### System
```
GET  /                              # API info
GET  /health                        # Health check
```

---

## 🐛 Troubleshooting

### Common Errors and Solutions

#### 1. Invalid Email Format

**Error Message:**
```
❌ Invalid email format. Please use format: user@example.com
```

**Solution:**
- Ensure email has `@` symbol
- Domain must have extension (`.com`, `.org`, etc.)
- Example: `patient@hospital.com`

---

#### 2. Password Too Short

**Error Message:**
```
❌ Password must be at least 6 characters long
```

**Solution:**
- Use 6 or more characters
- Example: `password123`

---

#### 3. Phone Number Invalid

**Error Message:**
```
❌ Phone number must contain at least 10 digits
```

**Solution:**
- Include at least 10 digits
- Format doesn't matter: `+1234567890` or `1234567890` both work

---

#### 4. API Connection Failed

**Error Message:**
```
⚠️ Cannot connect to backend API
```

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend
cd backend
uvicorn main:app --reload
```

---

#### 5. MongoDB Connection Error

**Error Message:**
```
❌ MongoDB connection failed
```

**Solution:**
1. Check `MONGODB_URI` in `.env`
2. Verify MongoDB Atlas cluster is running
3. Whitelist your IP in MongoDB Atlas
4. Test connection:
```python
python -c "from pymongo import MongoClient; MongoClient('YOUR_URI').server_info()"
```

---

#### 6. Port Already in Use

**Windows:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -i :8000
kill -9 <PID>
```

---

## 📊 Project Structure

```
IIS_Project_G13_Web/
│
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── api/
│   │   ├── middleware/
│   │   │   └── auth.py           # JWT authentication
│   │   └── routes/
│   │       ├── auth.py           # Login/register
│   │       ├── patients.py       # Patient endpoints
│   │       ├── doctors.py        # Doctor endpoints
│   │       └── admin.py          # Admin endpoints
│   ├── core/
│   │   ├── config.py             # Settings
│   │   ├── database.py           # MongoDB & encryption
│   │   └── llm.py                # AI integration
│   ├── models/
│   │   └── patient.py            # Pydantic models
│   └── requirements.txt
│
├── frontend/
│   ├── app.py                    # Streamlit UI
│   └── requirements.txt
│
├── shared/
│   └── knowledge_base.json       # Medical knowledge
│
├── .env.example                  # Environment template
├── start_dev.bat                 # Windows startup
├── start_dev.sh                  # Linux/Mac startup
├── DEPLOYMENT_GUIDE.md
├── INTERVIEW_PREP_WEB.md
└── README_WEB.md                 # This file
```

---

## 🚢 Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions:

- **Option 1:** Render (Backend) + Streamlit Cloud (Frontend)
- **Option 2:** Docker Compose
- **Option 3:** AWS EC2

---

## 🗺️ Roadmap

- [ ] Email verification
- [ ] Password reset functionality
- [ ] Two-factor authentication (2FA)
- [ ] PDF report generation
- [ ] Appointment scheduling
- [ ] Video consultations
- [ ] Mobile app (React Native)
- [ ] Real-time notifications
- [ ] Analytics dashboard

---

## 📄 License

MIT License - See LICENSE file

---

## 🤝 Support

- **Documentation:** [README_WEB.md](README_WEB.md)
- **Deployment:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Interview Prep:** [INTERVIEW_PREP_WEB.md](INTERVIEW_PREP_WEB.md)
- **API Docs:** http://localhost:8000/docs
- **Issues:** GitHub Issues

---

## 📞 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI, Streamlit, and MongoDB**