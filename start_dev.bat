@echo off
echo 🚀 Starting Medical Health Assessment System
echo ==========================================

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install backend dependencies
echo 📦 Installing backend dependencies...
cd backend
pip install -r requirements.txt
cd ..

REM Install frontend dependencies
echo 📦 Installing frontend dependencies...
cd frontend
pip install -r requirements.txt
cd ..

REM Start backend (new window)
echo 🔧 Starting backend API on port 8000...
start cmd /k "call venv\Scripts\activate && cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 5 >nul

REM Start frontend (new window)
echo 🎨 Starting frontend on port 8501...
start cmd /k "call venv\Scripts\activate && cd frontend && streamlit run app.py"

echo.
echo ✅ System is running!
echo 📊 Frontend: http://localhost:8501
echo 🔌 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Close the opened terminal windows to stop services.
pause
