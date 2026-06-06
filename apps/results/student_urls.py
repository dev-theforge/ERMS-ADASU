from django.urls import path
from . import student_views

app_name = 'student'

urlpatterns = [
    path('dashboard/', student_views.student_dashboard, name='dashboard'),
    path('results/', student_views.student_results, name='results'),
    path('results/download/<int:semester_id>/', student_views.download_result_slip, name='download_result_slip'),
    path('transcript/', student_views.download_transcript, name='transcript'),
    path('academic-history/', student_views.academic_history, name='academic_history'),
]
