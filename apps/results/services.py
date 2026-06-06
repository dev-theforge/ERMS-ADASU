"""GPA/CGPA calculation engine and result processing services."""
import csv
import io
from decimal import Decimal
from django.utils import timezone
from .models import Result, SemesterGPA, StudentCGPA, ResultUploadLog
from apps.accounts.models import StudentProfile, Course, Semester, GradeScale, CourseAssignment
from apps.notifications.models import Notification
from django.conf import settings


def compute_semester_gpa(student, semester):
    """Compute and persist GPA for a student in a semester."""
    results = Result.objects.filter(student=student, semester=semester, status='published')
    total_cu = sum(r.course.credit_units for r in results)
    total_qp = sum(float(r.quality_points) for r in results)
    gpa = round(total_qp / total_cu, 2) if total_cu else 0.0

    obj, _ = SemesterGPA.objects.update_or_create(
        student=student, semester=semester,
        defaults={'total_credit_units': total_cu, 'total_quality_points': total_qp, 'gpa': gpa}
    )
    # GPA warning notification
    threshold = getattr(settings, 'GPA_WARNING_THRESHOLD', 1.5)
    if gpa < threshold:
        Notification.notify(
            student.user, 'gpa_warning',
            'Low GPA Alert',
            f'Your GPA for {semester} is {gpa:.2f}, which is below the minimum threshold of {threshold}. Please seek academic counselling.',
        )
    return obj


def compute_student_cgpa(student):
    """Compute and persist CGPA for a student across all published results."""
    results = Result.objects.filter(student=student, status='published')
    total_cu = sum(r.course.credit_units for r in results)
    total_qp = sum(float(r.quality_points) for r in results)
    cgpa = round(total_qp / total_cu, 2) if total_cu else 0.0

    obj, _ = StudentCGPA.objects.update_or_create(
        student=student,
        defaults={'total_accumulated_credit_units': total_cu, 'total_accumulated_quality_points': total_qp, 'cgpa': cgpa}
    )
    return obj


def recompute_all_gpa_for_semester(semester):
    """Recompute GPA/CGPA for all students with published results in a semester."""
    student_ids = Result.objects.filter(semester=semester, status='published').values_list('student_id', flat=True).distinct()
    for sid in student_ids:
        try:
            student = StudentProfile.objects.get(pk=sid)
            compute_semester_gpa(student, semester)
            compute_student_cgpa(student)
        except StudentProfile.DoesNotExist:
            pass


def process_csv_upload(lecturer, semester, file_obj, multi_course=False):
    """
    Parse and validate a CSV upload from a lecturer.
    Returns (results_list, errors_list, stats_dict)
    """
    results_created = []
    errors = []
    total = 0

    try:
        content = file_obj.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
    except Exception as e:
        return [], [f"File read error: {e}"], {'total': 0, 'success': 0, 'failed': 1}

    for i, row in enumerate(rows, start=2):
        total += 1
        try:
            if multi_course:
                course_code = str(row.get('course_code', '')).strip().upper()
                matric_no = str(row.get('matric_no', '')).strip().upper()
                score_raw = str(row.get('score', '')).strip()
            else:
                course_code = None
                matric_no = str(row.get('matric_no', '')).strip().upper()
                score_raw = str(row.get('score', '')).strip()

            # Validate score
            try:
                score = Decimal(score_raw)
                if not (0 <= score <= 100):
                    raise ValueError()
            except Exception:
                errors.append(f"Row {i}: Invalid score '{score_raw}'")
                continue

            # Validate student
            try:
                student = StudentProfile.objects.get(matric_number=matric_no)
            except StudentProfile.DoesNotExist:
                errors.append(f"Row {i}: Student '{matric_no}' not found")
                continue

            # Resolve course
            if multi_course:
                try:
                    course = Course.objects.get(code=course_code, is_active=True)
                except Course.DoesNotExist:
                    errors.append(f"Row {i}: Course '{course_code}' not found")
                    continue
                # Verify lecturer is assigned to this course
                if not CourseAssignment.objects.filter(lecturer=lecturer, course=course, semester=semester).exists():
                    errors.append(f"Row {i}: You are not assigned to course '{course_code}' this semester")
                    continue
            else:
                # For single-course upload, course must be provided separately
                # We'll handle this via view context
                errors.append(f"Row {i}: Internal error — use multi-course upload path")
                continue

            # Check for existing published/approved result
            existing = Result.objects.filter(student=student, course=course, semester=semester).first()
            if existing:
                if existing.status in ['published', 'approved']:
                    errors.append(f"Row {i}: Result for {matric_no} in {course_code} already {existing.status} — cannot overwrite")
                    continue
                existing.score = score
                existing.lecturer = lecturer
                existing.save()
                results_created.append(existing)
            else:
                result = Result.objects.create(
                    student=student, course=course, semester=semester,
                    lecturer=lecturer, score=score, status='draft'
                )
                results_created.append(result)

        except Exception as e:
            errors.append(f"Row {i}: Unexpected error — {e}")

    return results_created, errors, {'total': total, 'success': len(results_created), 'failed': len(errors)}


def process_single_course_csv(lecturer, semester, course, file_obj):
    """Parse CSV for a single course (matric_no, score format)."""
    results_created = []
    errors = []
    total = 0

    try:
        content = file_obj.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
    except Exception as e:
        return [], [f"File read error: {e}"], {'total': 0, 'success': 0, 'failed': 1}

    for i, row in enumerate(rows, start=2):
        total += 1
        try:
            matric_no = str(row.get('matric_no', '')).strip().upper()
            score_raw = str(row.get('score', '')).strip()

            try:
                score = Decimal(score_raw)
                if not (0 <= score <= 100):
                    raise ValueError()
            except Exception:
                errors.append(f"Row {i}: Invalid score '{score_raw}'")
                continue

            try:
                student = StudentProfile.objects.get(matric_number=matric_no)
            except StudentProfile.DoesNotExist:
                errors.append(f"Row {i}: Student '{matric_no}' not found")
                continue

            existing = Result.objects.filter(student=student, course=course, semester=semester).first()
            if existing:
                if existing.status in ['published', 'approved']:
                    errors.append(f"Row {i}: Result for {matric_no} already {existing.status}")
                    continue
                existing.score = score
                existing.lecturer = lecturer
                existing.save()
                results_created.append(existing)
            else:
                result = Result.objects.create(
                    student=student, course=course, semester=semester,
                    lecturer=lecturer, score=score, status='draft'
                )
                results_created.append(result)

        except Exception as e:
            errors.append(f"Row {i}: {e}")

    return results_created, errors, {'total': total, 'success': len(results_created), 'failed': len(errors)}
