# Wellness Program Management System

A full-stack Django web application for organizations to run employee and student wellness programs, monitor daily biometrics, track session attendance, and deliver privacy-first aggregate HR analytics.

## Tech Stack
- **Backend:** Python Django 5.x
- **Frontend:** Django Templates, Bootstrap 5, Chart.js
- **Database:** SQLite (local dev), PostgreSQL (production via dj-database-url)
- **Static Files & Server:** WhiteNoise, Gunicorn
- **Deployment:** Render (Free Tier Blueprint with PostgreSQL)

## Demo Accounts (Password: `Demo@1234`)
| Role | Username | Password | Purpose |
|------|----------|----------|---------|
| Administrator | `admin_demo` | `Demo@1234` | System users, roles & category management |
| Coordinator | `coord_demo` | `Demo@1234` | Create programs, schedule sessions & record attendance |
| Professional | `pro_demo` | `Demo@1234` | Clinical notes & personalized wellness guidance |
| HR / Management | `hr_demo` | `Demo@1234` | Aggregate intelligence & population outcomes |
| Participant | `user_demo` | `Demo@1234` | Enroll, log daily habits & track reward eligibility |

## Business Rules
- **Participation Rate:** (Sessions Attended / Sessions Conducted) × 100
- **Reward Status:** Participation rate ≥ 75% unlocks "Eligible for Reward" status and bonus points.
- **Capacity Limits:** Programs cannot exceed max participant capacity; duplicate enrollments are rejected.
- **Privacy Protection:** Individual personal health logs and notes are strictly hidden from HR views.

## Local Setup
```bash
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

## Running Automated Tests
```bash
python manage.py test
```
