# ERMS — Online Examination Results Management System

**Rev. Fr. Moses Orshio Adasu University (Formerly Benue State University), Makurdi, Benue State, Nigeria**

---

## Overview

A complete, production-ready web-based platform for managing university examination results, supporting four user roles with automated GPA/CGPA calculation, complaint management, parent monitoring, PDF exports, and comprehensive reporting.

## Tech Stack

| Layer      | Technology                               |
| ---------- | ---------------------------------------- |
| Backend    | Django 4.2, Django ORM                   |
| Frontend   | Bootstrap 5.3, HTML5, CSS3, JS, Chart.js |
| Database   | SQLite (dev) / PostgreSQL (production)   |
| Auth       | Django Auth + Role-Based Access Control  |
| Deployment | Docker, Gunicorn, Nginx                  |
| Email      | SendGrid                                 |
| SMS        | Twilio                                   |
| Task Queue | Celery + Redis                           |

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment file
cp .env.example .env

# 4. Run migrations
python manage.py migrate

# 5. Seed initial data (creates demo accounts)
python manage.py seed_data

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Start development server
python manage.py runserver
```

Open **http://127.0.0.1:8000**

## Demo Accounts (after seed_data)

| Role     | Username | Password    |
| -------- | -------- | ----------- |
| Admin    | admin    | Admin@1234  |
| Lecturer | lec001   | Lec@12345   |
| Student  | stu001   | Stu@12345   |
| Parent   | parent01 | Parent@1234 |

## Project Structure

```
erms/
├── erms_project/          # Django project config (settings, urls, wsgi)
├── apps/
│   ├── accounts/          # CustomUser, all profiles, RBAC, admin views
│   ├── results/           # Results model, GPA engine, CSV upload, PDF
│   ├── complaints/        # Complaint lifecycle management
│   ├── notifications/     # In-app + email + SMS notifications
│   ├── feedback/          # Feedback & satisfaction surveys
│   ├── reports/           # Analytics, exports (PDF, CSV)
│   └── audit/             # AuditLog model + middleware
├── templates/             # 51 HTML templates (Bootstrap 5)
├── static/                # CSS (erms.css) + JS (erms.js)
├── docker/                # Dockerfile, docker-compose.yml, nginx.conf
└── docs/                  # INSTALLATION.md, USER_MANUAL.md
```

## Key Features

- Role-Based Access Control (Admin / Lecturer / Student / Parent)
- Automated grade + GPA + CGPA calculation (NUC scale)
- CSV bulk score upload (single-course & multi-course formats)
- Result approval workflow: Draft → Submitted → Approved → Published
- PDF result slips and full academic transcripts (ReportLab)
- Student complaint portal with admin review workflow
- Parent dashboard with ward monitoring and GPA trend charts
- In-app notifications + SendGrid email + Twilio SMS
- Reports: student, department, course, GPA distribution
- Audit logging for all system actions
- Docker + Nginx + PostgreSQL production deployment
- NDPR (Nigeria Data Protection Regulation) compliant

## Production Deployment

```bash
cd docker
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_data
```

See `docs/INSTALLATION.md` for full deployment guide.

---

_© Adasu University ERMS — Built with Django & Bootstrap 5_
