# 🏥 Medical Health Assessment System

AI-powered healthcare assessment system with multilingual support, built with FastAPI, Streamlit, and MongoDB.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-red)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)

**🌐 Live Demo:** [Your URL Here - Add after deployment]

---

## ✨ Key Features

- 🤖 **AI-Powered Symptom Analysis** - Mistral-7B LLM integration for clinical insights
- 🌍 **Multilingual Support** - 30+ languages with automatic translation
- 🔒 **Enterprise Security** - AES-256 encryption + JWT authentication
- 👥 **Role-Based Access** - Patient, Doctor, and Admin dashboards
- 📄 **PDF Reports** - Generate health assessment reports with Unicode support
- 🔄 **Real-Time Analysis** - Instant symptom detection and follow-up questions

---

## 🏗️ Architecture
```
User Browser
    ↓
Streamlit Frontend (Port 8501)
    ↓ REST API
FastAPI Backend (Port 8000)
    ↓ Encrypted Storage
MongoDB Atlas (Cloud)
```

**Tech Stack:**
- **Backend:** FastAPI, PyMongo, Cryptography, JWT
- **Frontend:** Streamlit, Requests
- **Database:** MongoDB Atlas with field-level encryption
- **AI/ML:** Mistral-7B (local), Google Translate API
- **Deployment:** Render.com (backend), Streamlit Cloud (frontend)

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- MongoDB Atlas account (free tier)
- Git

### Installation

**1. Clone Repository**
```bash
git clone https://github.com/yourusername/IIS_Project_G13_Web.git
cd IIS_Project_G13_Web
```

**2. Create Virtual Environment**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
cd ../frontend
pip install -r requirements.txt
cd ..
```

**4. Configure Environment**
```bash
copy .env.example .env
notepad .env
```

Fill in your MongoDB URI and secret keys.

**5. Run Application**
```bash
start_dev.bat
```

**Access:**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔐 Security Features

- ✅ **AES-256 Encryption** - All patient data encrypted at rest
- ✅ **JWT Authentication** - Stateless token-based auth with 24-hour expiration
- ✅ **Bcrypt Password Hashing** - Industry-standard password security
- ✅ **Role-Based Authorization** - Granular access control
- ✅ **CORS Protection** - Configured for production domains
- ✅ **Input Validation** - Pydantic models with strict type checking

---

## 📊 System Capabilities

### For Patients
- Register with natural language symptom description
- AI analyzes symptoms and generates follow-up questions
- View encrypted health records
- Download PDF health reports
- Multilingual interface (30+ languages)

### For Doctors
- View all patient records
- Generate AI-powered clinical insights
- Download patient PDF reports
- Search patients by name/email
- Access detailed symptom analysis

### For Admins
- Approve/reject doctor registrations
- View system statistics
- Manage user accounts
- Create additional admins

---

## 🌐 Deployment

**Production deployment uses:**
- ✅ Template-based summaries (instant response)
- ✅ Cloud-hosted MongoDB Atlas
- ✅ HTTPS with TLS 1.3
- ✅ Environment-based configuration

**Note:** The system supports both template-based and AI-powered (Mistral-7B) clinical summaries. The deployed version uses templates for performance. Full LLM integration is available in the codebase for local testing.

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

---

## 📁 Project Structure
```
IIS_Project_G13_Web/
├── backend/                 # FastAPI REST API
│   ├── api/
│   │   ├── middleware/      # JWT auth middleware
│   │   └── routes/          # API endpoints
│   ├── core/                # Config, database, LLM
│   ├── models/              # Pydantic models
│   ├── utils/               # PDF generation, etc.
│   └── main.py              # Entry point
├── frontend/                # Streamlit UI
│   └── app.py               # Main application
├── shared/                  # Shared resources
│   └── knowledge_base.json  # Medical symptoms database
├── .env.example             # Environment template
├── start_dev.bat            # Windows dev startup
└── requirements.txt         # Dependencies
```

---

## 🧪 API Endpoints

### Authentication
```
POST /api/auth/patient/register  - Patient registration
POST /api/auth/patient/login     - Patient login
POST /api/auth/doctor/login      - Doctor login
POST /api/auth/admin/login       - Admin login
```

### Patients
```
GET  /api/patients/me                    - Get current patient
PUT  /api/patients/me                    - Update patient info
POST /api/patients/analyze-symptoms      - Analyze symptoms
GET  /api/patients/me/pdf                - Download PDF report
POST /api/patients/me/change-password    - Change password
```

### Doctors
```
GET  /api/patients/                           - List all patients
GET  /api/patients/{id}                       - Get patient details
GET  /api/patients/{id}/pdf                   - Download patient PDF
POST /api/patients/{id}/clinical-insights     - Generate AI insights
```

### Admin
```
GET  /api/admin/doctors/pending      - Pending approvals
POST /api/admin/doctors/approve      - Approve/reject doctor
GET  /api/admin/patients/all         - List all patients
POST /api/admin/create               - Create new admin
```

Full API documentation: `http://localhost:8000/docs`

---

## 🛠️ Configuration

### Environment Variables
```env
# Database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB=health_chatbot_db

# Security
SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_KEY=your-encryption-key

# LLM (Optional)
USE_LLM=False                    # Set True for AI summaries
HUGGING_FACE_TOKEN=token         # Required if USE_LLM=True

# Frontend
FRONTEND_URL=http://localhost:8501
```

---

## 🤝 Contributing

This is a course project. Not accepting contributions at this time.

---

## 📄 License

MIT License - See LICENSE file

---

## 👨‍💻 Developer

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- **Course:** IIS Project (2nd Year)
- **Duration:** 2 weeks development
- **Institution:** Your College Name

---

**Built with ❤️ using FastAPI, Streamlit, and MongoDB**