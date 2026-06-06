# ERMS User Manual

**Online Examination Results Management System**
**Rev. Fr. Moses Orshio Adasu University, Makurdi**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Getting Started](#getting-started)
3. [Administrator Guide](#administrator-guide)
4. [Lecturer Guide](#lecturer-guide)
5. [Student Guide](#student-guide)
6. [Parent/Guardian Guide](#parentguardian-guide)
7. [Complaint Process](#complaint-process)
8. [GPA & CGPA Calculation](#gpa--cgpa-calculation)

---

## System Overview

ERMS is a web-based platform that digitalizes examination result management at Adasu University. The system supports four roles: **Administrator**, **Lecturer**, **Student**, and **Parent/Guardian**.

### Key Features

- Automated grade computation using NUC grading scale
- Semester GPA and cumulative CGPA calculation
- CSV bulk score upload
- Result approval workflow (Draft → Submitted → Approved → Published)
- Student complaint portal
- Parent monitoring dashboard
- PDF result slips and transcripts
- Comprehensive reporting and analytics
- SendGrid email + Twilio SMS notifications

---

## Getting Started

### Registration

1. Navigate to the ERMS portal home page
2. Click **Register** and select your role (Student / Lecturer / Parent)
3. Fill in all required fields accurately
4. Submit registration — your account is **pending admin approval**
5. You will receive an email notification when approved

### Login

1. Go to **Login** page
2. Enter your **username** and **password**
3. Click **Sign In**
4. You are redirected to your role-specific dashboard

---

## Administrator Guide

### Dashboard

The admin dashboard shows:
- Total counts: students, lecturers, parents, courses
- Pending approvals and complaints
- Published results count
- Recent registrations and system activity

### User Management

**Approve Users:**
1. Go to **Admin Panel → Users**
2. Filter by Status: Pending
3. Click **✓ Approve** or **✗ Reject** per user
4. The user receives an email notification

**Deactivate/Reactivate Accounts:**
- Locate the user in Users list
- Use **Deactivate** or **Activate** buttons

### Academic Setup

Set up in this order:
1. **Faculties** — Add all university faculties
2. **Departments** — Add departments linked to faculties
3. **Academic Sessions** — e.g., "2023/2024", mark one as Current
4. **Semesters** — Add First and Second semesters per session; mark Current
5. **Grade Scales** — Verify the A-F scale (pre-seeded if using `seed_data`)
6. **Courses** — Add all courses with correct department, level, credit units

### Result Approval Workflow

1. **Approve Results:** Admin Panel → Approve Results
   - Select semester
   - Check/uncheck results
   - Click **Approve Selected** or **Reject Selected**

2. **Publish Results:** Admin Panel → Publish Results
   - Select semester
   - Review list of approved results
   - Click **Publish** — all students notified immediately

### Complaint Management

1. Go to **Complaints** in sidebar
2. Filter by status (Pending, Under Review, Resolved, Rejected)
3. Click **Review** on a complaint
4. Update status, write admin response, add comments
5. Student is notified automatically

### Reports

Available reports:
- **Student Report** — Full transcript with GPA history (PDF/CSV export)
- **Department Report** — Average CGPA, pass/fail rates (CSV export)
- **Course Report** — Grade distribution with charts
- **GPA Distribution** — Semester-wide GPA banding

---

## Lecturer Guide

### Dashboard

Shows assigned courses for current semester with score entry status.

### Entering Scores Manually

1. Go to **My Courses** or click course from Dashboard
2. Click **Enter Scores** for a course
3. Type score (0–100) for each student
4. Click **Save Scores** — saved as Draft
5. When ready, click **Submit for Approval**

### Uploading Scores via CSV

**Single Course:**
1. Go to **Upload CSV**
2. Select Upload Type: **Single Course**
3. Select the semester and course
4. Upload CSV with format:
   ```
   matric_no,score
   ADU/2021/0001,75
   ADU/2021/0002,68
   ```

**Multiple Courses:**
1. Select Upload Type: **Multiple Courses**
2. Select semester only
3. Upload CSV with format:
   ```
   course_code,matric_no,score
   CSC101,ADU/2021/0001,75
   MTH101,ADU/2021/0002,82
   ```

**Download CSV templates** from the upload page or dashboard.

### Submitting for Approval

- After entering/uploading scores, click **Submit for Approval** on the Enter Scores page
- This changes status from Draft → Submitted
- Admins receive a notification and can approve/reject
- You can track approval status on your dashboard

---

## Student Guide

### Dashboard

Shows:
- Current GPA and CGPA
- Enrolled courses for current semester
- Recent published results
- Complaints summary
- Unread notifications

### Viewing Results

1. Go to **My Results** in sidebar
2. Filter by semester or session
3. View scores, grades, and GPA per semester
4. Download result slips (PDF) per semester
5. Download full transcript (PDF) from top button

### Academic History

**Student → Academic History** shows complete academic record organized by session and semester, with GPA trend chart.

### Filing a Complaint

1. Go to **File Complaint**
2. Select the published result to dispute
3. Enter subject and detailed description
4. Click **Submit** — admin is notified
5. Track status at **My Complaints**

---

## Parent/Guardian Guide

### Linking a Ward

1. Go to **Link Ward** in sidebar
2. Enter your ward's matric number exactly
3. Click **Link Ward**
4. Ward's performance now appears on your dashboard

> You can link multiple wards. Contact admin if the matric number is not found.

### Viewing Ward Performance

**Dashboard** shows:
- Ward CGPA
- Current level and department
- Recent published results
- GPA trend

**Ward Results:** Click **View Results** under a ward to filter by semester.

**Ward History:** Full semester-by-semester GPA breakdown with trend chart.

### Notifications

You receive automatic notifications when:
- Your ward's results are published
- Your ward's GPA falls below threshold
- Complaint updates on your ward's account

---

## Complaint Process

### Status Flow

```
Pending → Under Review → Resolved
                      ↘ Rejected
```

| Status | Meaning |
|--------|---------|
| Pending | Submitted, not yet reviewed |
| Under Review | Admin is reviewing |
| Resolved | Complaint addressed |
| Rejected | Complaint dismissed |

### Student Steps

1. File complaint for a published result
2. Check **My Complaints** for status updates
3. View admin response in complaint detail
4. Add follow-up comments if needed

---

## GPA & CGPA Calculation

### Grading Scale (NUC Standard)

| Score Range | Grade | Grade Point |
|-------------|-------|-------------|
| 70 – 100    | A     | 5.0         |
| 60 – 69     | B     | 4.0         |
| 50 – 59     | C     | 3.0         |
| 45 – 49     | D     | 2.0         |
| 40 – 44     | E     | 1.0         |
| 0 – 39      | F     | 0.0         |

### GPA Formula

```
Quality Points = Grade Point × Credit Units

GPA = Total Quality Points ÷ Total Credit Units (for the semester)
```

### CGPA Formula

```
CGPA = Total Accumulated Quality Points ÷ Total Accumulated Credit Units (all semesters)
```

### Example

| Course | CU | Score | Grade | GP  | QP  |
|--------|----|-------|-------|-----|-----|
| CSC101 | 3  | 75    | A     | 5.0 | 15  |
| MTH101 | 3  | 65    | B     | 4.0 | 12  |
| ECO101 | 2  | 52    | C     | 3.0 | 6   |

**Total CU = 8 | Total QP = 33**
**GPA = 33 ÷ 8 = 4.13**

---

## Security & Privacy

- All passwords are hashed (bcrypt)
- Sessions expire after inactivity
- Role-based access: users only see their own data
- All actions are logged in the Audit Log
- System is NDPR (Nigeria Data Protection Regulation) compliant
- CSRF protection on all forms

---

*ERMS — Rev. Fr. Moses Orshio Adasu University, Makurdi, Benue State*
*For technical support contact: erms-support@adasu.edu.ng*
