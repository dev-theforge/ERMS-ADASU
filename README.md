# ERMS — Online Examination Results Management System

**Rev. Fr. Moses Orshio Adasu University (Formerly Benue State University), Makurdi, Benue State, Nigeria**

---

## Overview

ERMS (Examination Results Management System) is a comprehensive web-based platform developed to automate the management, processing, publication, and monitoring of university examination results.

The system supports multiple user roles including Administrators, Lecturers, Students, and Parents, while providing secure access control, GPA/CGPA computation, complaint management, notifications, reporting, audit logging, and academic record generation.

The platform is designed to improve transparency, reduce administrative workload, eliminate result-processing errors, and provide timely access to academic information.

---

## Tech Stack

| Layer              | Technology                                        |
| ------------------ | ------------------------------------------------- |
| Backend            | Django 4.2, Django ORM                            |
| Frontend           | Bootstrap 5.3, HTML5, CSS3, JavaScript, Chart.js  |
| Database           | SQLite (Development), PostgreSQL (Production)     |
| Authentication     | Django Authentication + Role-Based Access Control |
| Deployment         | Docker, Gunicorn, Nginx                           |
| Email Service      | SendGrid                                          |
| SMS Service        | Twilio                                            |
| Task Queue         | Celery + Redis                                    |
| Reporting          | ReportLab                                         |
| Charts & Analytics | Chart.js                                          |

---

## Core User Roles

### Administrator

Administrators can:

* Manage users and approvals
* Manage academic sessions and semesters
* Manage departments and programmes
* Approve submitted results
* Publish examination results
* View reports and analytics
* Manage complaints
* Monitor audit logs
* Configure system settings

### Lecturer

Lecturers can:

* View assigned courses
* Upload scores individually
* Upload scores via CSV
* Submit results for approval
* View course statistics
* Monitor student performance

### Student

Students can:

* View published results
* View GPA and CGPA
* Download result slips
* Download transcripts (if enabled)
* Submit complaints
* Receive notifications
* Track academic progress

### Parent

Parents can:

* Monitor linked student accounts
* View academic performance
* View GPA trends
* Receive notifications regarding wards

---

## Key Features

### Academic Result Management

* Course score entry
* Bulk CSV score upload
* Automated grade calculation
* Automated GPA calculation
* Automated CGPA calculation
* NUC grading scale support
* Result validation

### Workflow Management

* Draft → Submitted → Approved → Published workflow
* Lecturer submission process
* Administrative approval process
* Controlled publication process

### Student Services

* Result viewing portal
* GPA tracking
* Academic transcript generation
* Complaint management portal
* Notification center

### Notifications

* In-app notifications
* SendGrid email integration
* Twilio SMS integration
* Account approval notifications
* Result publication notifications
* Complaint status updates
* GPA warning notifications
* Password change alerts

### Reporting & Analytics

* Student reports
* Department reports
* Course reports
* GPA distribution analysis
* Performance dashboards
* Course statistics charts

### Security & Compliance

* Role-Based Access Control (RBAC)
* Audit logging
* Secure authentication
* Session management
* NDPR (Nigeria Data Protection Regulation) compliant

### Deployment

* Docker support
* PostgreSQL support
* Gunicorn support
* Nginx reverse proxy support
* Production-ready architecture

---

## Quick Start

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Copy Environment File

```bash
cp .env.example .env
```

Windows:

```bash
copy .env.example .env
```

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Seed Demo Data

```bash
python manage.py seed_data
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Start Development Server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000
```

---

## Demo Accounts

Created automatically by:

```bash
python manage.py seed_data
```

| Role     | Username | Password    |
| -------- | -------- | ----------- |
| Admin    | admin    | Admin@1234  |
| Lecturer | lec001   | Lec@12345   |
| Student  | stu001   | Stu@12345   |
| Parent   | parent01 | Parent@1234 |

---

## Project Structure

```text
erms/
├── erms_project/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── accounts/
│   ├── results/
│   ├── complaints/
│   ├── notifications/
│   ├── feedback/
│   ├── reports/
│   └── audit/
│
├── templates/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/
│
├── docs/
│
├── docker/
│
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Environment Variables

ERMS uses environment variables for configuration.

Create a `.env` file from `.env.example`.

### Core Django

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database

```env
DB_ENGINE=postgresql
DB_NAME=erms_db
DB_USER=erms_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### SendGrid

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
SENDGRID_API_KEY=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Twilio

```env
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+234xxxxxxxxxx
```

### Redis

```env
REDIS_URL=redis://localhost:6379/0
```

---

## Notification Configuration

### Email Notifications (SendGrid)

ERMS supports automated email notifications for:

* Account approval
* Account rejection
* Result publication
* Complaint updates
* GPA warnings
* Password changes
* General notifications

### Development Configuration

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Emails will be displayed in the terminal.

### Production Configuration

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
SENDGRID_API_KEY=YOUR_SENDGRID_API_KEY
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### SendGrid Setup

1. Create a SendGrid account.
2. Verify a Sender Identity.
3. Authenticate a domain (recommended).
4. Create an API key with Mail Send permissions.
5. Add the API key to the `.env` file.
6. Restart the application.

### Testing Email Delivery

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    subject="ERMS Test",
    message="This is a test email from ERMS.",
    from_email=None,
    recipient_list=["your-email@example.com"],
    fail_silently=False,
)
```

Expected output:

```python
1
```

A return value of `1` indicates successful delivery to the SMTP server.

---

### SMS Notifications (Twilio)

Configure:

```env
TWILIO_ACCOUNT_SID=YOUR_ACCOUNT_SID
TWILIO_AUTH_TOKEN=YOUR_AUTH_TOKEN
TWILIO_PHONE_NUMBER=+234XXXXXXXXXX
```

An active Twilio account is required for SMS delivery.

---

### Notification Channels

ERMS supports:

* In-app notifications
* Email notifications (SendGrid)
* SMS notifications (Twilio)

If external services are unavailable, in-app notifications remain available within the application.

---

## Production Deployment

### Docker Deployment

```bash
cd docker

docker-compose up -d --build

docker-compose exec web python manage.py migrate

docker-compose exec web python manage.py seed_data
```

### Services

Production deployment includes:

* Django Application
* PostgreSQL Database
* Nginx Reverse Proxy
* Gunicorn Application Server
* Redis
* Celery Workers

Refer to:

```text
docs/INSTALLATION.md
```

for complete deployment instructions.

---

## Testing Checklist

Before production deployment verify:

### User Management

* [ ] User registration
* [ ] User approval
* [ ] User rejection
* [ ] Password reset
* [ ] Role permissions

### Results Workflow

* [ ] Score entry
* [ ] CSV upload
* [ ] Result submission
* [ ] Result approval
* [ ] Result publication
* [ ] GPA calculation
* [ ] CGPA calculation

### Notifications

* [ ] In-app notifications
* [ ] Email notifications
* [ ] SMS notifications

### Reports

* [ ] Student reports
* [ ] Department reports
* [ ] Course reports
* [ ] GPA distribution reports

### Documents

* [ ] Result slip PDF
* [ ] Academic transcript PDF

---

## License

Developed for:

**Rev. Fr. Moses Orshio Adasu University, Makurdi, Benue State, Nigeria**

---

© Adasu University ERMS — Built with Django, Bootstrap 5, Chart.js, SendGrid, and Twilio.
