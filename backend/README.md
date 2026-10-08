# 🏥 MediAssist AI
### AI-Powered Healthcare Assistance & Patient Management Platform

> **IMPORTANT MEDICAL SAFETY DISCLAIMER:**  
> **MediAssist AI** is an AI-powered healthcare assistance and educational decision-support platform — **not a diagnostic system**. It does **not** replace professional medical advice, diagnosis, or treatment. In case of emergency, call local emergency services immediately.

---

## 🚀 Overview

MediAssist AI is a complete, production-grade healthcare technology platform built with **FastAPI**, **PostgreSQL / SQLAlchemy**, **Pydantic V2**, **JWT Security**, and a **Multi-Layer AI Decision-Support Pipeline**.

### Key Features Across Phases 1–5:

1. **Phase 1 — Database & Authentication**:
   - PostgreSQL schema with UUID primary keys, relationships, and index optimizations.
   - Dual JWT Authentication (`access_token` and `refresh_token`).
   - Role-Based Access Control (RBAC): `patient`, `doctor`, `admin`.
   - Security Audit Logging system.

2. **Phase 2 — Patient & Doctor Management**:
   - Multi-criteria Doctor Search & Directory (by department, specialization, consultation fee, experience, name search, availability).
   - Real-time Doctor Availability Toggling.
   - Admin Statistics Dashboard with 14-day patient-registration and appointment trends, plus Doctor Credential Verification.
   - Role-based account profile photos for patients, doctors, and administrators (JPEG, PNG, WebP; max 2 MB).

3. **Phase 3 — Appointment System & Double-Booking Prevention**:
   - Database-level double-booking prevention (`UniqueConstraint("doctor_id", "appointment_date", "start_time")`).
   - Dynamic 30-minute time slot availability calculation engine.
   - Full Appointment Lifecycle (`pending` ➔ `confirmed` ➔ `completed` / `cancelled` / `rejected`).

4. **Phase 4 — Medical Records & Prescriptions**:
   - Electronic Health Records (EHR) & Prescription Management.
   - Upload metadata tracking for Medical Documents (PDFs, Lab Reports, Images).
   - Strict Ownership Authorization Guard (Patients can only view their own medical records).

5. **Phase 5 — Multi-Layer AI Symptom Assistant**:
   - **Input Validation Layer**: Text normalization & length validation.
   - **Emergency Safety Layer**: Real-time scanning for life-threatening emergency signals (chest pain, stroke symptoms, respiratory distress, anaphylaxis, seizures, suicidal crises).
   - **Symptom Extractor**: Clinical dictionary entity extraction.
   - **Medical Knowledge Retrieval Engine**: Pattern matching against clinical evidence knowledge base.
   - **Risk & Urgency Assessment Model**: Weighted priority scoring (`LOW`, `MODERATE`, `HIGH`, `EMERGENCY`).
   - **Safety Post-Processing Guard**: Enforces mandatory disclaimers and strips forbidden diagnostic phrases.
   - **Modular Provider Interface**: Abstract provider interface for offline rule engine or LLM integration.

---

## 🛠️ Installation & Quickstart

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (Optional for containerized PostgreSQL)

Copy `backend/.env.example` to `backend/.env` and set a unique `POSTGRES_PASSWORD`, a randomly generated `JWT_SECRET_KEY` (for example, `openssl rand -hex 32`), and a private `ADMIN_PASSWORD` before starting the application. Never commit `.env` files.

To start the Docker Compose services after configuring `backend/.env`:

```bash
docker compose --env-file backend/.env up --build
```

### Running Locally with Virtual Environment

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Set `ADMIN_EMAIL` and a private `ADMIN_PASSWORD` in `backend/.env`. The password is required when creating the initial administrator account.

3. Initialize database and seed default departments & admin account:
   ```bash
   python init_db.py
   ```

4. Start FastAPI Uvicorn Server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

5. Access Interactive Documentation:
   - **Swagger UI**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) (also available in the Admin dashboard)
   - **ReDoc**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

---

## 🧪 Running Automated Tests

Run the complete integration test suite covering Phases 1–5:

```bash
python -m pytest tests -v
```

Profile photos are uploaded through `POST /api/v1/users/me/avatar` and can be removed through `DELETE /api/v1/users/me/avatar`. Photo bytes are stored in the database and served through the authenticated `GET /api/v1/users/{user_id}/avatar` endpoint; only the photo owner and administrators can retrieve them. Public doctor directory photos use `GET /api/v1/doctors/{doctor_id}/avatar`. Existing `avatar_url` values and local photo files remain supported for compatibility.

### Patient and Doctor Password Reset

Password reset sends a one-time link to active patient and doctor accounts. Configure Gmail SMTP in `backend/.env` using `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USE_STARTTLS=True`, the Gmail account in `SMTP_USER` and `SMTP_FROM_EMAIL`, and a Google App Password in `SMTP_PASSWORD`. Do not use a Gmail sign-in password or commit the `.env` file. Set `FRONTEND_BASE_URL` to the URL patients and doctors use to access the frontend (the local instance defaults to `http://localhost:5175`; change it if Vite is using a different port). Reset links expire after 30 minutes by default.

The app provides `POST /api/v1/auth/password/forgot` and `POST /api/v1/auth/password/reset`. Reset tokens are random, single-use, expire after the configured duration, and only their SHA-256 hashes are stored. Request responses do not disclose whether an email belongs to an account. If SMTP is not configured, password-reset requests return a service-unavailable response.

Patient platform feedback is saved for administrator review and sent by email when SMTP is configured. `FEEDBACK_RECIPIENT_EMAIL` defaults to `sanjays60641@gmail.com`; patient submissions use `POST /api/v1/feedback/`. Configure the Gmail App Password settings above to enable email delivery. If SMTP is missing or delivery fails, feedback remains saved and appears in the administrator dashboard under **Patient feedback**. Administrators can retry email delivery after correcting the SMTP settings.

### Deploying to Render

The root `render.yaml` Blueprint deploys the FastAPI API and Vite frontend as separate Render services. Select **New > Blueprint** in Render and connect this repository. During initial setup, provide the existing Neon PostgreSQL `DATABASE_URL`; Render generates a fresh `JWT_SECRET_KEY`. The Blueprint shares the API and frontend hostnames so the frontend API URL and backend CORS origin stay aligned.

The existing Neon database already contains the seeded administrator and departments. Keep the same database when deploying this app; do not run `init_db.py` against a new production database until you intend to initialize it. Configure SMTP environment variables in the API service to enable password-reset and feedback emails.

The Blueprint uses Render's free web-service plan, which sleeps when idle and has an ephemeral filesystem. New profile photos are stored in the configured PostgreSQL database, so they remain available after service restarts and redeployments. The first API request after inactivity can still take about a minute. Do not store real patient health information on a demo deployment; review applicable privacy, security, and compliance requirements before production use.

---

## 📄 License
Educational & Demonstration License — MediAssist AI Project 2026.
