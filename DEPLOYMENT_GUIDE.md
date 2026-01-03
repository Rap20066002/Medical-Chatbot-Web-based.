# 🚀 Deployment Guide - Medical Health Assessment System

Complete guide to deploy your application on Render.com (backend) and Streamlit Cloud (frontend).

**Estimated Time:** 2 hours  
**Cost:** $0 (using free tiers)

---

## 📋 Prerequisites

Before you start:

- ✅ GitHub account (create at github.com)
- ✅ MongoDB Atlas account with database created
- ✅ Your project code ready

---

## 🎯 Deployment Overview

```
GitHub Repository
    ├── Render.com (Backend API)
    └── Streamlit Cloud (Frontend UI)
         ↓
    MongoDB Atlas (Database)
```

---

## 📦 STEP 1: Push to GitHub (30 minutes)

### 1.1 Create GitHub Repository

1. Go to **github.com**
2. Click **"New repository"** (green button)
3. **Repository name:** `healthcare-assessment-system`
4. **Description:** `AI-powered healthcare assessment with multilingual support`
5. **Visibility:** Public (so Render/Streamlit can access)
6. **DON'T** check "Initialize with README" (we have one)
7. Click **"Create repository"**

### 1.2 Initialize Git (if not already)

Open Command Prompt in your project folder:

```bash
cd C:\Users\zeega\OneDrive\Desktop\IIS_Project_G13_Web
```

Check if Git is initialized:
```bash
git status
```

**If you see:** `fatal: not a git repository`

Then initialize:
```bash
git init
git add .
git commit -m "Initial commit: Healthcare Assessment System"
```

**If you already have Git initialized**, skip to next step.

### 1.3 Connect to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/healthcare-assessment-system.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME`** with your GitHub username!

**If prompted for credentials:**
- Username: your GitHub username
- Password: Create a **Personal Access Token** (not your password!)
  - Go to GitHub.com → Settings → Developer settings → Personal access tokens → Generate new token
  - Check "repo" scope
  - Copy token and use as password

### 1.4 Verify Upload

Go to your GitHub repository in browser - you should see all your files! ✅

---

## 🔧 STEP 2: Deploy Backend on Render.com (30 minutes)

### 2.1 Create Render Account

1. Go to **render.com**
2. Click **"Get Started"**
3. Sign up with GitHub (easiest)
4. Authorize Render to access your repositories

### 2.2 Create Web Service

1. Click **"New +"** → **"Web Service"**
2. **Connect repository:** Select `healthcare-assessment-system`
3. Click **"Connect"**

### 2.3 Configure Service

**Basic Settings:**
- **Name:** `healthcare-backend` (or your choice)
- **Region:** Choose closest to you
- **Branch:** `main`
- **Root Directory:** `backend` ⚠️ **IMPORTANT!**
- **Runtime:** `Python 3`

**Build Settings:**
- **Build Command:**
  ```bash
  pip install -r requirements.txt
  ```

- **Start Command:**
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 10000
  ```

**Instance Type:**
- Select **"Free"** ($0/month)

### 2.4 Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these **one by one**:

```env
MONGODB_URI
# Paste your MongoDB Atlas connection string
# Example: mongodb+srv://username:password@cluster.mongodb.net/

MONGODB_DB
# Value: health_chatbot_db

SECRET_KEY
# Generate a random string (32+ characters)
# Example: your-super-secret-key-change-this-in-production

ENCRYPTION_KEY
# Generate using Python:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Paste the output here

USE_LLM
# Value: False

FRONTEND_URL
# Value: https://healthcare-frontend.streamlit.app
# (We'll update this after frontend deployment)

DEBUG
# Value: False
```

**How to generate ENCRYPTION_KEY (on Windows):**

Open Command Prompt:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output (looks like: `xFJk8L4N...`)

### 2.5 Deploy!

1. Click **"Create Web Service"**
2. **Wait 5-10 minutes** (Render installs dependencies)
3. Watch the logs - should see:
   ```
   ✅ MongoDB connection successful
   ✅ Encryption initialized
   ✅ Application ready!
   ```

### 2.6 Get Your Backend URL

Once deployed, you'll see:
```
Your service is live at https://healthcare-backend.onrender.com
```

**Copy this URL!** You'll need it for frontend.

### 2.7 Test Backend

Open in browser:
```
https://healthcare-backend.onrender.com/health
```

Should see:
```json
{
  "status": "healthy",
  "database": "connected",
  "llm": "unavailable"
}
```

✅ **Backend deployed!**

---

## 🎨 STEP 3: Deploy Frontend on Streamlit Cloud (30 minutes)

### 3.1 Create Streamlit Account

1. Go to **share.streamlit.io**
2. Click **"Sign up"**
3. **Sign in with GitHub** (recommended)
4. Authorize Streamlit

### 3.2 Deploy App

1. Click **"New app"**
2. **Repository:** Select `healthcare-assessment-system`
3. **Branch:** `main`
4. **Main file path:** `frontend/app.py` ⚠️ **IMPORTANT!**
5. **App URL:** Choose your subdomain
   - Example: `healthcare-frontend` → `healthcare-frontend.streamlit.app`

### 3.3 Add Secrets

Click **"Advanced settings"** → **"Secrets"**

Add this (in TOML format):

```toml
API_BASE_URL = "https://healthcare-backend.onrender.com"
```

**⚠️ Replace** `healthcare-backend.onrender.com` **with YOUR Render URL from Step 2.6!**

### 3.4 Deploy!

1. Click **"Deploy!"**
2. **Wait 3-5 minutes** (installs dependencies)
3. Watch logs for:
   ```
   ✅ Backend API connected!
   ```

### 3.5 Get Your Frontend URL

You'll see:
```
https://healthcare-frontend.streamlit.app
```

**This is your live app!** 🎉

---

## 🔄 STEP 4: Update CORS (5 minutes)

Now that you have your frontend URL, update backend CORS:

### 4.1 Go to Render Dashboard

1. Open **render.com**
2. Go to your **healthcare-backend** service
3. Click **"Environment"**

### 4.2 Update FRONTEND_URL

Find `FRONTEND_URL` variable and change to:
```
https://healthcare-frontend.streamlit.app
```

(Use YOUR actual Streamlit URL!)

### 4.3 Redeploy

Click **"Manual Deploy"** → **"Deploy latest commit"**

Wait 2-3 minutes for restart.

---

## ✅ STEP 5: Test Everything (15 minutes)

### 5.1 Test Patient Registration

1. Go to your Streamlit URL
2. Click **"Patient Registration"** tab
3. Fill form with test data:
   - Name: Test Patient
   - Age: 25
   - Email: test@example.com
   - Phone: 1234567890
   - Password: test123
   - Symptoms: "I have headache and fever for 3 days"
4. Click **"Analyze My Symptoms"**
5. Should see detected symptoms ✅
6. Click **"Complete Registration"**
7. Should login automatically ✅

### 5.2 Test Doctor Login

1. Register a doctor (will need admin approval)
2. Login as admin (create first admin if none exists)
3. Approve doctor
4. Login as doctor
5. View patient records ✅

### 5.3 Test PDF Download

1. Login as patient
2. Go to **"Profile"** tab
3. Click **"Download PDF Report"**
4. Should download PDF ✅

---

## 🎯 STEP 6: Update Documentation (10 minutes)

### 6.1 Update README.md

Replace this line:
```markdown
**🌐 Live Demo:** [Your URL Here]
```

With:
```markdown
**🌐 Live Demo:** https://healthcare-frontend.streamlit.app
```

### 6.2 Update Your Resume

Add to your resume:
```
Healthcare Assessment System | FastAPI, Streamlit, MongoDB
• Deployed full-stack application with 30+ language support
• Live at: healthcare-frontend.streamlit.app
• GitHub: github.com/username/healthcare-assessment-system
```

### 6.3 Push Updates

```bash
git add README.md
git commit -m "Update README with live demo URL"
git push
```

---

## 📊 Monitoring & Maintenance

### Check Backend Logs

Render.com Dashboard → Your service → **"Logs"** tab

### Check Frontend Logs

Streamlit Cloud → Your app → **"Manage app"** → **"Logs"**

### Update Code

```bash
# Make changes locally
git add .
git commit -m "Your update message"
git push

# Backend: Auto-redeploys (Render watches GitHub)
# Frontend: Auto-redeploys (Streamlit watches GitHub)
```

---

## 🐛 Troubleshooting

### Backend shows "Service Unavailable"

**Check:**
1. Environment variables set correctly?
2. MongoDB Atlas IP whitelist → Allow access from anywhere (0.0.0.0/0)
3. Check logs in Render dashboard

**Fix:** Ensure `MONGODB_URI` is correct and MongoDB allows connections.

### Frontend can't connect to backend

**Check:**
1. `API_BASE_URL` in Streamlit secrets correct?
2. Backend URL ends with `.onrender.com` (no trailing slash)?
3. Backend is actually running? (test `/health` endpoint)

**Fix:** Update Streamlit secrets with correct backend URL.

### "Cannot connect to database"

**Check:**
1. MongoDB Atlas cluster is running?
2. Database user credentials correct in `MONGODB_URI`?
3. IP whitelist allows 0.0.0.0/0?

**Fix:** In MongoDB Atlas → Network Access → Add IP Address → Allow access from anywhere.

### Deployment fails on Render

**Check logs for:**
- Dependency installation errors → Check `requirements.txt`
- Port binding errors → Ensure using `--port 10000`
- Import errors → Check all files committed to GitHub

### Streamlit app crashes

**Check:**
- Backend URL correct in secrets?
- All dependencies in `requirements.txt`?
- No missing files in GitHub?

---

## 💡 Pro Tips

### Free Tier Limitations

**Render.com (Free):**
- ✅ Sleeps after 15 min inactivity
- ⏱️ First request takes 30-60s to wake up
- ✅ Good enough for portfolio/resume
- 💡 Upgrade to $7/month for always-on

**Streamlit Cloud (Free):**
- ✅ Always on
- ✅ Unlimited apps (public repos)
- ✅ Auto-updates from GitHub

### Performance Optimization

**If backend is slow:**
1. Ensure `USE_LLM=False` (already set ✅)
2. Add indexes to MongoDB (see docs)
3. Enable caching in Streamlit

### Security Checklist

- ✅ `DEBUG=False` in production
- ✅ Strong `SECRET_KEY` (32+ characters)
- ✅ Unique `ENCRYPTION_KEY`
- ✅ Never commit `.env` file
- ✅ MongoDB user has read/write only (not admin)

---

## 🎉 Success!

You now have:

- ✅ Backend API running on Render.com
- ✅ Frontend UI on Streamlit Cloud
- ✅ Database on MongoDB Atlas
- ✅ HTTPS enabled (automatic)
- ✅ Auto-deployment from GitHub
- ✅ Professional portfolio project

**Share your live URL with recruiters!** 🚀

---

## 📞 Need Help?

**If stuck:**
1. Check logs (Render/Streamlit dashboards)
2. Google error messages
3. Check MongoDB Atlas network access
4. Verify environment variables

**Common URLs to check:**
- Backend health: `https://your-backend.onrender.com/health`
- API docs: `https://your-backend.onrender.com/docs`
- Frontend: `https://your-app.streamlit.app`

---

**Deployment Complete! Time to update your resume and start applying! 💼**