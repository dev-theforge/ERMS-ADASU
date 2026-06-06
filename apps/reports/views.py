import csv
import io
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Avg, Count, Q
from apps.accounts.decorators import admin_required, lecturer_required
from apps.accounts.models import StudentProfile, Department, Faculty, AcademicSession, Semester, Course
from apps.results.models import Result, SemesterGPA, StudentCGPA


@admin_required
def reports_home(request):
    return render(request, 'reports/home.html')


@admin_required
def student_report(request, matric_number=None):
    search = request.GET.get('matric', matric_number or '')
    student = None
    results = []
    gpa_records = []
    cgpa_obj = None
    if search:
        try:
            student = StudentProfile.objects.select_related('user', 'department__faculty').get(matric_number=search)
            results = Result.objects.filter(student=student, status='published').select_related('course', 'semester__session').order_by('semester__session__start_date')
            gpa_records = SemesterGPA.objects.filter(student=student).select_related('semester__session').order_by('semester__session__start_date')
            cgpa_obj = getattr(student, 'cgpa_record', None)
        except StudentProfile.DoesNotExist:
            pass

    if request.GET.get('export') == 'csv' and student:
        return _export_student_csv(student, results, gpa_records, cgpa_obj)
    if request.GET.get('export') == 'pdf' and student:
        from apps.results.pdf_generator import generate_transcript
        from django.http import HttpResponse
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="transcript_{student.matric_number}.pdf"'
        generate_transcript(response, student, results, gpa_records, cgpa_obj)
        return response

    return render(request, 'reports/student_report.html', {
        'student': student, 'results': results, 'gpa_records': gpa_records,
        'cgpa': cgpa_obj, 'search': search
    })


@admin_required
def department_report(request):
    departments = Department.objects.filter(is_active=True).select_related('faculty')
    dept_id = request.GET.get('dept')
    session_id = request.GET.get('session')
    data = None

    if dept_id:
        dept = get_object_or_404(Department, pk=dept_id)
        students = StudentProfile.objects.filter(department=dept)
        cgpa_records = StudentCGPA.objects.filter(student__in=students)
        avg_cgpa = cgpa_records.aggregate(avg=Avg('cgpa'))['avg'] or 0
        results = Result.objects.filter(student__in=students, status='published')
        if session_id:
            results = results.filter(semester__session_id=session_id)
        pass_count = results.filter(~Q(grade='F')).count()
        fail_count = results.filter(grade='F').count()
        total = results.count()

        data = {
            'dept': dept,
            'total_students': students.count(),
            'avg_cgpa': round(avg_cgpa, 2),
            'pass_count': pass_count,
            'fail_count': fail_count,
            'pass_rate': round(pass_count / total * 100, 1) if total else 0,
        }

    if request.GET.get('export') == 'csv' and data:
        return _export_department_csv(data)

    sessions = AcademicSession.objects.order_by('-start_date')
    return render(request, 'reports/department_report.html', {
        'departments': departments, 'data': data,
        'sessions': sessions, 'selected_dept': dept_id, 'selected_session': session_id
    })


@admin_required
def course_report(request):
    semester_id = request.GET.get('semester')
    course_id = request.GET.get('course')
    semesters = Semester.objects.select_related('session').order_by('-session__start_date')
    courses = Course.objects.filter(is_active=True).select_related('department')
    data = None

    if course_id and semester_id:
        course = get_object_or_404(Course, pk=course_id)
        semester = get_object_or_404(Semester, pk=semester_id)
        results = Result.objects.filter(course=course, semester=semester, status='published').select_related('student__user')
        total = results.count()
        grade_dist = {}
        for r in results:
            grade_dist[r.grade] = grade_dist.get(r.grade, 0) + 1
        avg_score = results.aggregate(avg=Avg('score'))['avg'] or 0
        pass_count = results.filter(~Q(grade='F')).count()
        data = {
            'course': course, 'semester': semester,
            'results': results, 'total': total,
            'grade_dist': grade_dist, 'avg_score': round(avg_score, 2),
            'pass_count': pass_count, 'fail_count': total - pass_count,
            'pass_rate': round(pass_count / total * 100, 1) if total else 0,
        }

    return render(request, 'reports/course_report.html', {
        'semesters': semesters, 'courses': courses, 'data': data,
        'selected_semester': semester_id, 'selected_course': course_id
    })


@admin_required
def gpa_distribution_report(request):
    semester_id = request.GET.get('semester')
    semesters = Semester.objects.select_related('session').order_by('-session__start_date')
    dist_data = None
    if semester_id:
        semester = get_object_or_404(Semester, pk=semester_id)
        gpas = SemesterGPA.objects.filter(semester=semester).values_list('gpa', flat=True)
        dist = {'5.0': 0, '4.0–4.9': 0, '3.0–3.9': 0, '2.0–2.9': 0, '1.0–1.9': 0, 'Below 1.0': 0}
        for g in gpas:
            g = float(g)
            if g >= 4.5: dist['5.0'] += 1
            elif g >= 3.5: dist['4.0–4.9'] += 1
            elif g >= 2.5: dist['3.0–3.9'] += 1
            elif g >= 1.5: dist['2.0–2.9'] += 1
            elif g >= 1.0: dist['1.0–1.9'] += 1
            else: dist['Below 1.0'] += 1
        dist_data = {'semester': semester, 'distribution': dist, 'total': len(gpas)}
    return render(request, 'reports/gpa_distribution.html', {'semesters': semesters, 'data': dist_data, 'selected': semester_id})


def _export_student_csv(student, results, gpa_records, cgpa_obj):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="report_{student.matric_number}.csv"'
    w = csv.writer(response)
    w.writerow(['Academic Report:', student.user.get_full_name(), student.matric_number])
    w.writerow([])
    w.writerow(['Course Code', 'Course Title', 'Credit Units', 'Score', 'Grade', 'Grade Point', 'Quality Points', 'Semester'])
    for r in results:
        w.writerow([r.course.code, r.course.title, r.course.credit_units, r.score, r.grade, r.grade_point, r.quality_points, str(r.semester)])
    w.writerow([])
    w.writerow(['CGPA', cgpa_obj.cgpa if cgpa_obj else 'N/A'])
    return response


def _export_department_csv(data):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="dept_report_{data["dept"].code}.csv"'
    w = csv.writer(response)
    w.writerow(['Department', data['dept'].name, data['dept'].code])
    w.writerow(['Total Students', data['total_students']])
    w.writerow(['Average CGPA', data['avg_cgpa']])
    w.writerow(['Pass Count', data['pass_count']])
    w.writerow(['Fail Count', data['fail_count']])
    w.writerow(['Pass Rate (%)', data['pass_rate']])
    return response
