# ERMS Installation Guide

**Rev. Fr. Moses Orshio Adasu University, Makurdi**
**Online Examination Results Management System**

---

## Prerequisites

- Python 3.11+
- pip
- Git
- (Production) PostgreSQL 15+, Redis 7+, Docker, Docker Compose

---

## Development Setup (SQLite)

### 1. Clone / Extract Project

```bash
cd /your/projects/folder
# Extract the ERMS zip or clone repo
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate          # Linux/macOS
venv\Scripts\activate             # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env — no changes needed for SQLite development
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Seed Initial Data (Recommended)

```bash
python manage.py seed_data
```

This creates:
| Role     | Username  | Password     |
|----------|-----------|--------------|
| Admin    | admin     | Admin@1234   |
| Lecturer | lec001    | Lec@12345    |
| Student  | stu001    | Stu@12345    |
| Parent   | parent01  | Parent@1234  |

### 7. Collect Static Files

```bash
python manage.py collectstatic
```

### 8. Run Development Server

```bash
python manage.py runserver
```

Open: **http://127.0.0.1:8000**

---

## Production Setup (PostgreSQL + Docker)

### 1. Configure Production Environment

```bash
cp .env.example .env.production
```

Edit `.env.production`:

```env
SECRET_KEY=<generate-64-char-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_ENGINE=postgresql
DB_NAME=erms_db
DB_USER=erms_user
DB_PASSWORD=<strong-password>
DB_HOST=db
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
SENDGRID_API_KEY=<your-sendgrid-key>
DEFAULT_FROM_EMAIL=noreply@adasu.edu.ng

REDIS_URL=redis://redis:6379/0
```

### 2. Generate Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Build and Start Docker

```bash
cd docker
docker-compose up -d --build
```

### 4. Run Migrations in Container

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_data
docker-compose exec web python manage.py createsuperuser
```

### 5. Check Services

```bash
docker-compose ps
docker-compose logs web
```

Access: **http://yourdomain.com**

---

## Email Configuration (SendGrid)

1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Create an API Key with "Mail Send" permission
3. Add to `.env`:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
   ```

---

## SMS Configuration (Twilio)

1. Sign up at [twilio.com](https://twilio.com)
2. Get Account SID, Auth Token, and a phone number
3. Add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxx
   TWILIO_PHONE_NUMBER=+1234567890
   ```

---

## Admin Setup Checklist

After first login as `admin`:

1. **Admin Panel → Grade Scales** — Verify A/B/C/D/E/F scale
2. **Admin Panel → Sessions** — Create current academic session
3. **Admin Panel → Semesters** — Create and mark current semester
4. **Admin Panel → Faculties** — Add faculties
5. **Admin Panel → Departments** — Add departments under faculties
6. **Admin Panel → Courses** — Add all courses
7. **Admin Panel → Users** — Approve lecturer/student/parent registrations
8. **Assign Courses** — Assign courses to lecturers via Django Admin (CourseAssignment)

---

## Project Structure

```
erms/
├── erms_project/        # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/        # Users, profiles, RBAC
│   ├── results/         # Results, GPA engine, CSV upload
│   ├── complaints/      # Complaint management
│   ├── notifications/   # In-app notifications
│   ├── feedback/        # Feedback & surveys
│   ├── reports/         # Analytics & exports
│   └── audit/           # Audit logging
├── templates/           # All HTML templates
├── static/              # CSS, JS, images
├── media/               # Uploaded files
├── docker/              # Docker & Nginx config
└── docs/                # Documentation
```
