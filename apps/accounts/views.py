from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import (
    CustomUser, StudentProfile, LecturerProfile, ParentProfile,
    Department, Faculty, AcademicSession, Semester, Course, GradeScale, Enrollment
)
from .forms import (
    LoginForm, StudentRegistrationForm, LecturerRegistrationForm,
    ParentRegistrationForm, UserProfileUpdateForm, ChangePasswordForm, LinkWardForm
)
from .decorators import admin_required, student_required, parent_required, lecturer_required
from apps.notifications.models import Notification
from apps.audit.models import AuditLog


def landing_view(request):
    if request.user.is_authenticated and request.user.status == 'active':
        return redirect('dashboard')
    return render(request, 'accounts/landing.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.status == 'pending':
            messages.warning(request, "Your account is awaiting admin approval.")
            return redirect('accounts:login')
        if user.status == 'rejected':
            messages.error(request, "Your registration has been rejected. Contact support.")
            return redirect('accounts:login')
        if user.status == 'inactive':
            messages.error(request, "Your account has been deactivated. Contact support.")
            return redirect('accounts:login')
        login(request, user)
        AuditLog.log(user=user, action='User logged in', ip=request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
        return redirect('dashboard')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        AuditLog.log(user=request.user, action='User logged out', ip=request.META.get('REMOTE_ADDR'))
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')


def register_view(request):
    return render(request, 'accounts/register_select.html')


def register_student(request):
    form = StudentRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Registration submitted! Await administrator approval.")
        return redirect('accounts:login')
    return render(request, 'accounts/register_student.html', {'form': form, 'title': 'Student Registration'})


def register_lecturer(request):
    form = LecturerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Registration submitted! Await administrator approval.")
        return redirect('accounts:login')
    return render(request, 'accounts/register_lecturer.html', {'form': form, 'title': 'Lecturer Registration'})


def register_parent(request):
    form = ParentRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Registration submitted! Await administrator approval.")
        return redirect('accounts:login')
    return render(request, 'accounts/register_parent.html', {'form': form, 'title': 'Parent/Guardian Registration'})


@login_required
def dashboard_redirect(request):
    role = request.user.role
    if role == 'admin':
        return redirect('admin_panel:dashboard')
    elif role == 'lecturer':
        return redirect('lecturer:dashboard')
    elif role == 'student':
        return redirect('student:dashboard')
    elif role == 'parent':
        return redirect('parent:dashboard')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    form = UserProfileUpdateForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        AuditLog.log(user=request.user, action='Updated profile')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    form = ChangePasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = request.user
        if not user.check_password(form.cleaned_data['old_password']):
            messages.error(request, "Old password is incorrect.")
        else:
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            update_session_auth_hash(request, user)
            Notification.notify(
                recipient=user,
                ntype='password_changed',
                title='Password Changed',
                message=(
                    'Your ERMS account password was changed successfully. '
                    'If you did not make this change, contact support immediately at erms-support@adasu.edu.ng.'
                ),
            )
            AuditLog.log(user=user, action='Changed password')
            messages.success(request, "Password changed successfully.")
            return redirect('accounts:profile')
    return render(request, 'accounts/change_password.html', {'form': form})


# ─── ADMIN PANEL VIEWS ────────────────────────────────────────────────────────

@admin_required
def admin_dashboard(request):
    from apps.results.models import Result
    from apps.complaints.models import Complaint
    context = {
        'total_students': StudentProfile.objects.count(),
        'total_lecturers': LecturerProfile.objects.count(),
        'total_parents': ParentProfile.objects.count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_results': Result.objects.count(),
        'pending_approvals': CustomUser.objects.filter(status='pending').count(),
        'pending_complaints': Complaint.objects.filter(status='pending').count(),
        'published_results': Result.objects.filter(status='published').count(),
        'recent_users': CustomUser.objects.order_by('-date_joined')[:10],
        'recent_activity': AuditLog.objects.select_related('user').order_by('-timestamp')[:15],
        'sessions': AcademicSession.objects.all()[:5],
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_users(request):
    role_filter   = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search        = request.GET.get('q', '')
    users = CustomUser.objects.all()
    if role_filter:
        users = users.filter(role=role_filter)
    if status_filter:
        users = users.filter(status=status_filter)
    if search:
        users = (
            users.filter(username__icontains=search) |
            users.filter(first_name__icontains=search) |
            users.filter(last_name__icontains=search) |
            users.filter(email__icontains=search)
        )
    from django.core.paginator import Paginator
    paginator = Paginator(users.order_by('-date_joined'), 25)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'admin_panel/users.html', {
        'page_obj': page,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search': search,
    })


@admin_required
def admin_approve_user(request, pk):
    user   = get_object_or_404(CustomUser, pk=pk)
    action = request.POST.get('action')

    if action == 'approve':
        user.status    = 'active'
        user.is_active = True
        user.save()
        Notification.notify(
            recipient=user,
            ntype='account_approval',
            title='Account Approved — Welcome to ERMS',
            message=(
                f'Congratulations {user.get_full_name()}! '
                f'Your registration on the ERMS portal has been approved by the administrator. '
                f'You can now log in with your username and password to access the portal.'
            ),
        )
        AuditLog.log(request.user, f'Approved account for {user.username}')
        messages.success(request, f"{user.get_full_name()} approved successfully.")

    elif action == 'reject':
        user.status = 'rejected'
        user.save()
        Notification.notify(
            recipient=user,
            ntype='account_rejection',
            title='Account Registration Not Approved',
            message=(
                f'Dear {user.get_full_name()}, your registration on the ERMS portal '
                f'has been reviewed and was not approved at this time. '
                f'Please contact the Academic Affairs office for further information.'
            ),
        )
        AuditLog.log(request.user, f'Rejected account for {user.username}')
        messages.warning(request, f"{user.get_full_name()} rejected.")

    elif action == 'deactivate':
        user.status    = 'inactive'
        user.is_active = False
        user.save()
        AuditLog.log(request.user, f'Deactivated account for {user.username}')
        messages.info(request, f"{user.get_full_name()} deactivated.")

    elif action == 'activate':
        user.status    = 'active'
        user.is_active = True
        user.save()
        AuditLog.log(request.user, f'Re-activated account for {user.username}')
        messages.success(request, f"{user.get_full_name()} re-activated.")

    return redirect('admin_panel:users')


@admin_required
def admin_faculties(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        desc = request.POST.get('description', '')
        Faculty.objects.create(name=name, code=code, description=desc)
        messages.success(request, "Faculty created.")
        AuditLog.log(request.user, f'Created faculty: {name}')
    faculties = Faculty.objects.all().order_by('name')
    return render(request, 'admin_panel/faculties.html', {'faculties': faculties})


@admin_required
def admin_departments(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        faculty_id = request.POST.get('faculty')
        dept = Department.objects.create(name=name, code=code, faculty_id=faculty_id)
        messages.success(request, f"Department {dept.code} created.")
    depts    = Department.objects.select_related('faculty').order_by('name')
    faculties = Faculty.objects.filter(is_active=True)
    return render(request, 'admin_panel/departments.html', {
        'departments': depts, 'faculties': faculties
    })


@admin_required
def admin_sessions(request):
    if request.method == 'POST':
        name       = request.POST.get('name')
        start      = request.POST.get('start_date')
        end        = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'on'
        AcademicSession.objects.create(name=name, start_date=start, end_date=end, is_current=is_current)
        messages.success(request, f"Session {name} created.")
    sessions = AcademicSession.objects.prefetch_related('semesters').order_by('-start_date')
    return render(request, 'admin_panel/sessions.html', {'sessions': sessions})


@admin_required
def admin_semesters(request):
    if request.method == 'POST':
        session_id = request.POST.get('session')
        sem_type   = request.POST.get('semester_type')
        start      = request.POST.get('start_date')
        end        = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'on'
        Semester.objects.create(
            session_id=session_id, semester_type=sem_type,
            start_date=start, end_date=end, is_current=is_current
        )
        messages.success(request, "Semester created.")
    semesters = Semester.objects.select_related('session').order_by('-session__start_date', 'semester_type')
    sessions  = AcademicSession.objects.all()
    return render(request, 'admin_panel/semesters.html', {
        'semesters': semesters, 'sessions': sessions
    })


@admin_required
def admin_courses(request):
    if request.method == 'POST':
        Course.objects.create(
            code=request.POST.get('code'),
            title=request.POST.get('title'),
            department_id=request.POST.get('department'),
            credit_units=request.POST.get('credit_units', 3),
            level=request.POST.get('level', 100),
            semester_type=request.POST.get('semester_type', 'first'),
        )
        messages.success(request, "Course created.")
    courses     = Course.objects.select_related('department__faculty').order_by('code')
    departments = Department.objects.filter(is_active=True).select_related('faculty')
    return render(request, 'admin_panel/courses.html', {
        'courses': courses, 'departments': departments
    })


@admin_required
def admin_grade_scales(request):
    if request.method == 'POST':
        GradeScale.objects.create(
            label=request.POST.get('label'),
            min_score=request.POST.get('min_score'),
            max_score=request.POST.get('max_score'),
            grade_point=request.POST.get('grade_point'),
            remark=request.POST.get('remark', ''),
        )
        messages.success(request, "Grade scale entry added.")
    scales = GradeScale.objects.order_by('-min_score')
    return render(request, 'admin_panel/grade_scales.html', {'scales': scales})


@admin_required
def admin_audit_logs(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'admin_panel/audit_logs.html', {'page_obj': page})


@admin_required
def admin_publish_results(request):
    from apps.results.models import Result
    from apps.results.services import recompute_all_gpa_for_semester

    semester_id       = request.GET.get('semester')
    semesters         = Semester.objects.select_related('session').order_by('-session__start_date')
    results           = []
    selected_semester = None

    if semester_id:
        selected_semester = get_object_or_404(Semester, pk=semester_id)
        results = Result.objects.filter(
            semester=selected_semester, status='approved'
        ).select_related('student__user', 'course')

    if request.method == 'POST':
        sem_id = request.POST.get('semester_id')
        sem    = get_object_or_404(Semester, pk=sem_id)

        # Publish all approved results for this semester
        approved = Result.objects.filter(semester=sem, status='approved')
        count    = approved.update(status='published', published_at=timezone.now())

        # Recompute GPA/CGPA for every affected student
        recompute_all_gpa_for_semester(sem)

        # --- Notify students ---
        student_ids = Result.objects.filter(
            semester=sem, status='published'
        ).values_list('student_id', flat=True).distinct()

        students = StudentProfile.objects.filter(
            pk__in=student_ids
        ).select_related('user')

        for sp in students:
            Notification.notify(
                recipient=sp.user,
                ntype='result_published',
                title=f'Results Published — {sem}',
                message=(
                    f'Your examination results for {sem} have been published on the ERMS portal. '
                    f'Log in to view your scores, grades, and GPA. '
                    f'You can also download your result slip from the portal.'
                ),
                url='/student/results/',
            )

        # --- Notify parents of those students ---
        from apps.accounts.models import ParentProfile
        parents = ParentProfile.objects.filter(
            wards__in=students
        ).select_related('user').distinct()

        for parent in parents:
            # Get ward names for this parent
            ward_names = ', '.join(
                w.user.get_full_name()
                for w in parent.wards.filter(pk__in=student_ids)
            )
            Notification.notify(
                recipient=parent.user,
                ntype='result_published',
                title=f'Ward Results Published — {sem}',
                message=(
                    f'The examination results for {sem} have been published for your ward(s): {ward_names}. '
                    f'Log in to the ERMS Parent Portal to view your ward\'s performance, '
                    f'GPA, and full academic report.'
                ),
                url='/parent/dashboard/',
            )

        AuditLog.log(request.user, f'Published {count} results for {sem}')
        messages.success(request, f"{count} results published for {sem}. Students and parents notified.")
        return redirect('admin_panel:publish_results')

    return render(request, 'admin_panel/publish_results.html', {
        'semesters': semesters,
        'results': results,
        'selected_semester': selected_semester,
    })


@admin_required
def admin_approve_results(request):
    from apps.results.models import Result

    semester_id       = request.GET.get('semester')
    semesters         = Semester.objects.select_related('session').order_by('-session__start_date')
    results           = Result.objects.none()
    selected_semester = None

    if semester_id:
        selected_semester = get_object_or_404(Semester, pk=semester_id)
        results = Result.objects.filter(
            semester=selected_semester, status='submitted'
        ).select_related('student__user', 'course', 'lecturer__user')

    if request.method == 'POST':
        action     = request.POST.get('action')
        result_ids = request.POST.getlist('result_ids')

        if action == 'approve' and result_ids:
            count = Result.objects.filter(
                pk__in=result_ids, status='submitted'
            ).update(
                status='approved',
                approved_by=request.user,
                approved_at=timezone.now()
            )
            AuditLog.log(request.user, f'Approved {count} results')
            messages.success(request, f"{count} result(s) approved.")

        elif action == 'reject' and result_ids:
            rejected = Result.objects.filter(pk__in=result_ids, status='submitted')
            # Notify lecturers whose results were rejected
            lecturer_users = set()
            for r in rejected.select_related('lecturer__user'):
                if r.lecturer:
                    lecturer_users.add(r.lecturer.user)
            count = rejected.update(status='rejected')
            for lu in lecturer_users:
                Notification.notify(
                    recipient=lu,
                    ntype='result_submitted',
                    title='Results Rejected — Action Required',
                    message=(
                        f'Some of your submitted results for {selected_semester} were rejected by the administrator. '
                        f'Please log in, review the results, make corrections, and resubmit.'
                    ),
                )
            AuditLog.log(request.user, f'Rejected {count} results')
            messages.warning(request, f"{count} result(s) rejected. Lecturers notified.")

        return redirect(f'/admin-panel/approve-results/?semester={semester_id}')

    return render(request, 'admin_panel/approve_results.html', {
        'semesters': semesters,
        'results': results,
        'selected_semester': selected_semester,
    })
