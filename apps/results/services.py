"""
GPA/CGPA calculation engine and result processing services.
All GPA warnings fire email + SMS automatically via Notification.notify().
"""
import csv
import io
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.conf import settings
from .models import Result, SemesterGPA, StudentCGPA, ResultUploadLog
from apps.accounts.models import StudentProfile, Course, Semester, GradeScale, CourseAssignment


# ─────────────────────────────────────────────────────────────────────────────
# GPA & CGPA ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def compute_semester_gpa(student, semester):
    """
    Compute and persist the GPA for one student in one semester.
    Also fires a GPA warning notification (email + SMS) if below threshold.
    Returns the SemesterGPA instance.
    """
    results   = Result.objects.filter(
        student=student, semester=semester, status='published'
    ).select_related('course')

    total_cu = sum(r.course.credit_units for r in results)
    total_qp = sum(float(r.quality_points) for r in results)
    gpa      = round(total_qp / total_cu, 2) if total_cu else 0.0

    obj, _ = SemesterGPA.objects.update_or_create(
        student=student,
        semester=semester,
        defaults={
            'total_credit_units':  total_cu,
            'total_quality_points': total_qp,
            'gpa': gpa,
        },
    )

    # Fire GPA warning if below threshold
    threshold = getattr(settings, 'GPA_WARNING_THRESHOLD', 1.5)
    if gpa < threshold:
        from apps.notifications.models import Notification
        Notification.notify(
            recipient=student.user,
            ntype='gpa_warning',
            title=f'Low GPA Alert — {semester}',
            message=(
                f'Your GPA for {semester} is {gpa:.2f}, which is below the '
                f'minimum acceptable threshold of {threshold:.1f}.\n\n'
                f'This may affect your academic standing. '
                f'Please visit the Academic Affairs office or your Head of Department '
                f'as soon as possible to discuss your academic progress and available support.'
            ),
        )

    return obj


def compute_student_cgpa(student):
    """
    Compute and persist the cumulative GPA for a student across all
    published results in all semesters. Returns the StudentCGPA instance.
    """
    results = Result.objects.filter(
        student=student, status='published'
    ).select_related('course')

    total_cu = sum(r.course.credit_units for r in results)
    total_qp = sum(float(r.quality_points) for r in results)
    cgpa     = round(total_qp / total_cu, 2) if total_cu else 0.0

    obj, _ = StudentCGPA.objects.update_or_create(
        student=student,
        defaults={
            'total_accumulated_credit_units':  total_cu,
            'total_accumulated_quality_points': total_qp,
            'cgpa': cgpa,
        },
    )
    return obj


def recompute_all_gpa_for_semester(semester):
    """
    Recompute GPA and CGPA for every student who has published results
    in the given semester. Called immediately after publishing results.
    """
    student_ids = Result.objects.filter(
        semester=semester, status='published'
    ).values_list('student_id', flat=True).distinct()

    for sid in student_ids:
        try:
            student = StudentProfile.objects.select_related('user').get(pk=sid)
            compute_semester_gpa(student, semester)
            compute_student_cgpa(student)
        except StudentProfile.DoesNotExist:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# CSV PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def _parse_score(raw):
    """Parse and validate a score value. Returns Decimal or raises ValueError."""
    try:
        score = Decimal(str(raw).strip())
    except InvalidOperation:
        raise ValueError(f"'{raw}' is not a valid number")
    if not (0 <= score <= 100):
        raise ValueError(f"Score {score} is out of range (must be 0–100)")
    return score


def process_single_course_csv(lecturer, semester, course, file_obj):
    """
    Parse a single-course CSV (columns: matric_no, score).
    Returns (results_list, errors_list, stats_dict).
    """
    results_saved = []
    errors        = []

    try:
        content = file_obj.read().decode('utf-8-sig').strip()
        reader  = csv.DictReader(io.StringIO(content))
        rows    = list(reader)
    except Exception as exc:
        return [], [f"Could not read file: {exc}"], {'total': 0, 'success': 0, 'failed': 1}

    # Validate headers
    required_cols = {'matric_no', 'score'}
    if reader.fieldnames:
        actual = {c.strip().lower() for c in reader.fieldnames}
        missing = required_cols - actual
        if missing:
            return [], [
                f"Missing required column(s): {', '.join(missing)}. "
                f"Expected headers: matric_no,score"
            ], {'total': 0, 'success': 0, 'failed': 1}

    total = len(rows)

    for i, row in enumerate(rows, start=2):
        matric_no = str(row.get('matric_no', '') or '').strip().upper()
        score_raw = str(row.get('score',    '') or '').strip()

        if not matric_no and not score_raw:
            total -= 1          # blank row — skip silently
            continue

        # Validate score
        try:
            score = _parse_score(score_raw)
        except ValueError as exc:
            errors.append(f"Row {i} ({matric_no}): {exc}")
            continue

        # Validate student
        try:
            student = StudentProfile.objects.get(matric_number=matric_no)
        except StudentProfile.DoesNotExist:
            errors.append(f"Row {i}: Student with matric number '{matric_no}' not found in the system")
            continue

        # Check for locked existing result
        existing = Result.objects.filter(
            student=student, course=course, semester=semester
        ).first()

        if existing:
            if existing.status in ('published', 'approved'):
                errors.append(
                    f"Row {i} ({matric_no}): Result already {existing.status} — cannot overwrite"
                )
                continue
            existing.score   = score
            existing.lecturer = lecturer
            existing.save()
            results_saved.append(existing)
        else:
            r = Result.objects.create(
                student=student, course=course, semester=semester,
                lecturer=lecturer, score=score, status='draft',
            )
            results_saved.append(r)

    return results_saved, errors, {
        'total':   total,
        'success': len(results_saved),
        'failed':  len(errors),
    }


def process_multi_course_csv(lecturer, semester, file_obj):
    """
    Parse a multi-course CSV (columns: course_code, matric_no, score).
    Returns (results_list, errors_list, stats_dict).
    """
    results_saved = []
    errors        = []

    try:
        content = file_obj.read().decode('utf-8-sig').strip()
        reader  = csv.DictReader(io.StringIO(content))
        rows    = list(reader)
    except Exception as exc:
        return [], [f"Could not read file: {exc}"], {'total': 0, 'success': 0, 'failed': 1}

    required_cols = {'course_code', 'matric_no', 'score'}
    if reader.fieldnames:
        actual  = {c.strip().lower() for c in reader.fieldnames}
        missing = required_cols - actual
        if missing:
            return [], [
                f"Missing required column(s): {', '.join(missing)}. "
                f"Expected headers: course_code,matric_no,score"
            ], {'total': 0, 'success': 0, 'failed': 1}

    total = len(rows)

    for i, row in enumerate(rows, start=2):
        course_code = str(row.get('course_code', '') or '').strip().upper()
        matric_no   = str(row.get('matric_no',   '') or '').strip().upper()
        score_raw   = str(row.get('score',        '') or '').strip()

        if not course_code and not matric_no and not score_raw:
            total -= 1
            continue

        # Validate score
        try:
            score = _parse_score(score_raw)
        except ValueError as exc:
            errors.append(f"Row {i} ({matric_no}): {exc}")
            continue

        # Validate student
        try:
            student = StudentProfile.objects.get(matric_number=matric_no)
        except StudentProfile.DoesNotExist:
            errors.append(f"Row {i}: Student '{matric_no}' not found")
            continue

        # Validate course
        try:
            course = Course.objects.get(code=course_code, is_active=True)
        except Course.DoesNotExist:
            errors.append(f"Row {i}: Course '{course_code}' not found or is inactive")
            continue

        # Verify the lecturer is assigned to this course this semester
        if not CourseAssignment.objects.filter(
            lecturer=lecturer, course=course, semester=semester
        ).exists():
            errors.append(
                f"Row {i}: You are not assigned to course '{course_code}' "
                f"for {semester} — cannot upload scores for it"
            )
            continue

        # Check for locked existing result
        existing = Result.objects.filter(
            student=student, course=course, semester=semester
        ).first()

        if existing:
            if existing.status in ('published', 'approved'):
                errors.append(
                    f"Row {i} ({matric_no}, {course_code}): "
                    f"Result already {existing.status} — cannot overwrite"
                )
                continue
            existing.score    = score
            existing.lecturer = lecturer
            existing.save()
            results_saved.append(existing)
        else:
            r = Result.objects.create(
                student=student, course=course, semester=semester,
                lecturer=lecturer, score=score, status='draft',
            )
            results_saved.append(r)

    return results_saved, errors, {
        'total':   total,
        'success': len(results_saved),
        'failed':  len(errors),
    }
