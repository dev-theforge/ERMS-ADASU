from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .decorators import parent_required
from .models import StudentProfile, ParentProfile
from .forms import LinkWardForm
from apps.results.models import Result, SemesterGPA, StudentCGPA
from apps.notifications.models import Notification
from apps.complaints.models import Complaint


@parent_required
def parent_dashboard(request):
    parent = request.user.parent_profile
    wards = parent.wards.select_related('user', 'department__faculty').all()
    ward_data = []
    for ward in wards:
        cgpa = getattr(ward, 'cgpa_record', None)
        recent_results = Result.objects.filter(student=ward, status='published').order_by('-semester__session__start_date')[:5]
        gpa_trend = SemesterGPA.objects.filter(student=ward).order_by('semester__session__start_date')[:6]
        ward_data.append({
            'ward': ward,
            'cgpa': cgpa,
            'recent_results': recent_results,
            'gpa_trend': list(gpa_trend),
        })
    notifications = Notification.objects.filter(recipient=request.user, is_read=False)[:5]
    return render(request, 'parent/dashboard.html', {
        'ward_data': ward_data,
        'notifications': notifications,
    })


@parent_required
def link_ward(request):
    form = LinkWardForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        matric = form.cleaned_data['matric_number']
        try:
            student = StudentProfile.objects.get(matric_number=matric)
            parent = request.user.parent_profile
            if parent.wards.filter(pk=student.pk).exists():
                messages.info(request, f"{student.user.get_full_name()} is already linked.")
            else:
                parent.wards.add(student)
                messages.success(request, f"Successfully linked to {student.user.get_full_name()}.")
        except StudentProfile.DoesNotExist:
            messages.error(request, f"No student found with matric number {matric}.")
        return redirect('parent:dashboard')
    return render(request, 'parent/link_ward.html', {'form': form})


@parent_required
def ward_results(request, ward_id):
    parent = request.user.parent_profile
    ward = get_object_or_404(parent.wards, pk=ward_id)
    from apps.accounts.models import Semester
    semester_id = request.GET.get('semester')
    semesters = Semester.objects.order_by('-session__start_date', 'semester_type')
    results = Result.objects.filter(student=ward, status='published').select_related('course', 'semester__session')
    if semester_id:
        results = results.filter(semester_id=semester_id)
    cgpa = getattr(ward, 'cgpa_record', None)
    return render(request, 'parent/ward_results.html', {
        'ward': ward, 'results': results, 'semesters': semesters, 'cgpa': cgpa,
        'selected_semester': semester_id,
    })


@parent_required
def ward_history(request, ward_id):
    parent = request.user.parent_profile
    ward = get_object_or_404(parent.wards, pk=ward_id)
    gpa_records = SemesterGPA.objects.filter(student=ward).select_related('semester__session').order_by('semester__session__start_date')
    cgpa = getattr(ward, 'cgpa_record', None)
    complaints = Complaint.objects.filter(student=ward).order_by('-created_at')[:10]
    return render(request, 'parent/ward_history.html', {
        'ward': ward, 'gpa_records': gpa_records, 'cgpa': cgpa, 'complaints': complaints
    })
