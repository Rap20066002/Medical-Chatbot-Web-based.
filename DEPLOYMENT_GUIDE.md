# 🚀 Deployment Guide – Medical Health Assessment Web App

This guide contains COMPLETE instructions to run and deploy the Medical Health Assessment Web App
on Windows, Linux, and macOS.

====================================================
PROJECT STRUCTURE
====================================================

IIS_Project_G13_Web/
│
├── backend/                 FastAPI backend
├── frontend/                Streamlit frontend
├── .env.example             Environment template
├── start_dev.bat            Windows startup script
├── start_dev.sh             Linux / macOS startup script
├── docker-compose.yml
└── DEPLOYMENT_GUIDE.md

====================================================
DEVELOPMENT SETUP
====================================================

STEP 1: CLONE REPOSITORY

    git clone <your-repo-url>
    cd IIS_Project_G13_Web


STEP 2: ENVIRONMENT VARIABLES

Windows (CMD / PowerShell):

    copy .env.example .env
    notepad .env

Linux / macOS:

    cp .env.example .env
    nano .env

Fill all required values (MongoDB, HuggingFace, Secret Keys).


STEP 3: CREATE VIRTUAL ENVIRONMENT

    python -m venv venv


STEP 4: ACTIVATE VIRTUAL ENVIRONMENT

Windows (CMD):

    venv\Scripts\activate

Windows (PowerShell):

    .\venv\Scripts\Activate.ps1

Linux / macOS:

    source venv/bin/activate


STEP 5: INSTALL DEPENDENCIES

Backend:

    cd backend
    pip install -r requirements.txt
    cd ..

Frontend:

    cd frontend
    pip install -r requirements.txt
    cd ..


STEP 6: START DEVELOPMENT SERVERS

OPTION A (RECOMMENDED): USING STARTUP SCRIPT

Windows:

    start_dev.bat

Linux / macOS:

    chmod +x start_dev.sh
    ./start_dev.sh


start_dev.bat (WINDOWS CONTENT):

    @echo off
    echo Starting Backend...
    start cmd /k "cd backend && ..\venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    timeout /t 3 > nul
    echo Starting Frontend...
    start cmd /k "cd frontend && ..\venv\Scripts\activate && streamlit run app.py"


start_dev.sh (LINUX / MAC CONTENT):

    #!/bin/bash
    echo "Starting Backend..."
    cd backend
    source ../venv/bin/activate
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    sleep 3
    echo "Starting Frontend..."
    cd ../frontend
    source ../venv/bin/activate
    streamlit run app.py


OPTION B: MANUAL START

Backend:

    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Frontend:

    cd frontend
    streamlit run app.py


STEP 7: ACCESS APPLICATION

Frontend:        http://localhost:8501
Backend API:     http://localhost:8000
Swagger Docs:    http://localhost:8000/docs

====================================================
PRODUCTION DEPLOYMENT
====================================================

OPTION 1: RENDER (BACKEND) + STREAMLIT CLOUD (FRONTEND)

Render Backend:

Build Command:
    cd backend && pip install -r requirements.txt

Start Command:
    cd backend && uvicorn main:app --host 0.0.0.0 --port 10000

Environment Variables:
    MONGODB_URI=
    SECRET_KEY=
    HUGGING_FACE_TOKEN=
    ENCRYPTION_KEY=
    FRONTEND_URL=


Streamlit Cloud Frontend:

Secrets:
    API_BASE_URL="https://your-backend.onrender.com"


OPTION 2: DOCKER (WINDOWS / LINUX / MAC)

Build & Start:
    docker-compose up -d

View Logs:
    docker-compose logs -f

Stop:
    docker-compose down


OPTION 3: AWS EC2 (UBUNTU 22.04)

Instance:
    t2.medium or higher
    Open ports: 22, 80, 443, 8000, 8501

Server Setup:
    sudo apt update && sudo apt upgrade -y
    sudo apt install python3-pip python3-venv nginx -y

App Setup:
    git clone <your-repo-url>
    cd IIS_Project_G13_Web
    python3 -m venv venv
    source venv/bin/activate

Install Dependencies:
    cd backend && pip install -r requirements.txt && cd ..
    cd frontend && pip install -r requirements.txt && cd ..

Environment Variables:
    cp .env.example .env
    nano .env

====================================================
SECURITY CHECKLIST
====================================================

- Change SECRET_KEY
- Use MongoDB Atlas with IP whitelist
- Enable HTTPS (Let’s Encrypt)
- Disable DEBUG mode
- Never commit .env
- Restrict CORS to frontend domain
- Enable rate limiting
- Enable logging & monitoring
- Regular database backups

====================================================
MONITORING & LOGS
====================================================

Health Check:
    GET /health

Docker Logs:
    docker-compose logs -f backend
    docker-compose logs -f frontend

Linux Systemd Logs:
    sudo journalctl -u health-backend -f
    sudo journalctl -u health-frontend -f

====================================================
TROUBLESHOOTING
====================================================

Check MongoDB Connection:
    python -c "from pymongo import MongoClient; MongoClient('your_uri').server_info()"

Port Already in Use (Windows):
    netstat -ano | findstr :8000
    taskkill /PID <PID> /F

Port Already in Use (Linux / macOS):
    lsof -i :8000
    kill -9 <PID>

====================================================
DONE
====================================================

Your Medical Health Assessment Web App is ready to run and deploy.
