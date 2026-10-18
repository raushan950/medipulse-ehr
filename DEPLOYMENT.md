# 🚀 MediPulse EHR — Deployment Guide (Render & Vercel)

This guide walks you through deploying **MediPulse EHR** to **Render** and **Vercel**, connecting both to a free cloud-hosted **MongoDB Atlas** cluster.

---

## 📋 Pre-requisite: Free MongoDB Atlas Cloud Database

Because Render and Vercel run on cloud servers, they cannot connect to `mongodb://localhost:27017/`. You will need a free cloud MongoDB database:

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and sign up / log in.
2. Click **Build a Database** and select the **M0 Free Tier** (AWS, choose the closest region to you).
3. Under **Security & Access**:
   - **Database User:** Create a username and password (e.g. `medipulse_admin` / `<secure-password>`). *Save this password.*
   - **Network Access:** Click **Add IP Address** $\rightarrow$ select **Allow Access from Anywhere (`0.0.0.0/0`)** so Render and Vercel can reach it.
4. Go to **Database** $\rightarrow$ Click **Connect** $\rightarrow$ **Drivers** (Python 3.12+).
5. Copy your connection URI string:
   ```
   mongodb+srv://medipulse_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
   ```
   *(Replace `<password>` with your database user password).*

---

## 🐙 Step 1: Push Project to GitHub

Both Render and Vercel deploy directly from your GitHub repository.

1. Create a new repository on [GitHub](https://github.com/new) named `medipulse-ehr` (leave it empty without README/license).
2. Open PowerShell in `c:\Users\DELL\OneDrive\Desktop\Nosql` and run:
   ```powershell
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/medipulse-ehr.git
   git branch -M main
   git push -u origin main
   ```

---

## 🌐 Deployment Method 1: Deploy on Render (Recommended for Flask)

Render runs Python Flask natively with Gunicorn, background tasks, and persistent sessions.

### Steps:
1. Log in to [Render.com](https://render.com/).
2. Click **New +** in the top right $\rightarrow$ select **Web Service**.
3. Connect your GitHub account and select your **`medipulse-ehr`** repository.
4. Configure the settings:
   - **Name:** `medipulse-ehr`
   - **Region:** Nearest to you (e.g. Singapore, Frankfurt, or Ohio)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`
5. Click **Advanced** $\rightarrow$ **Add Environment Variable**:
   | Key | Value |
   | :--- | :--- |
   | `MONGODB_URI` | `mongodb+srv://medipulse_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority` |
   | `DATABASE_NAME` | `medipulse_db` |
   | `FLASK_SECRET_KEY` | *(Click "Generate" or paste a random string)* |
   | `PYTHON_VERSION` | `3.12.10` |
6. Click **Create Web Service**.
7. Render will build and deploy your app. Once deployed, you will get a live URL (e.g., `https://medipulse-ehr.onrender.com`).

*(Note: The repository also includes [render.yaml](file:///c:/Users/DELL/OneDrive/Desktop/Nosql/render.yaml) which automatically configures these settings if you use Render Blueprints!)*

---

## ⚡ Deployment Method 2: Deploy on Vercel (Serverless Python)

Vercel runs the Flask application as an AWS Lambda serverless function via `@vercel/python`.

### Files Configured:
- `vercel.json` — Routes all web traffic to the serverless function.
- `api/index.py` — Serverless WSGI entrypoint that loads `app.py`.
- `.vercelignore` — Prevents test logs and unnecessary assets from being packaged.

### Steps:
1. Log in to [Vercel.com](https://vercel.com/).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your **`medipulse-ehr`** GitHub repository.
4. In the **Configure Project** screen:
   - **Framework Preset:** Select `Other`.
   - **Root Directory:** `./`
5. Expand the **Environment Variables** section and add:
   | Key | Value |
   | :--- | :--- |
   | `MONGODB_URI` | `mongodb+srv://medipulse_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority` |
   | `DATABASE_NAME` | `medipulse_db` |
   | `FLASK_SECRET_KEY` | *(A long random string)* |
6. Click **Deploy**.
7. In ~60 seconds, Vercel will complete the build and assign a live production URL (e.g., `https://medipulse-ehr.vercel.app`).

---

## 💻 Local Production WSGI (Windows / LAN)

If you also wish to serve this on your local machine or college intranet at full production performance without debug mode:
```powershell
python run_production.py
```
This runs the high-concurrency multi-threaded **Waitress WSGI** server listening on `http://0.0.0.0:5000/`.

---

## 🐳 Docker Stack (Zero-Setup Alternative)

To run the entire platform (Web App + MongoDB) isolated in Docker containers:
```powershell
docker compose up --build -d
```
Accessible at `http://localhost:5000/`.
