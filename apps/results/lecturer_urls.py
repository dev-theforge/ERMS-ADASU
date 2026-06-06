from django.urls import path
from . import lecturer_views

app_name = 'lecturer'

urlpatterns = [
    path('dashboard/', lecturer_views.lecturer_dashboard, name='dashboard'),
    path('courses/', lecturer_views.lecturer_courses, name='courses'),
    path('courses/<int:course_id>/semester/<int:semester_id>/enter-scores/', lecturer_views.lecturer_enter_scores, name='enter_scores'),
    path('courses/<int:course_id>/semester/<int:semester_id>/submit/', lecturer_views.submit_results, name='submit_results'),
    path('courses/<int:course_id>/semester/<int:semester_id>/stats/', lecturer_views.course_statistics, name='course_stats'),
    path('upload-csv/', lecturer_views.lecturer_upload_csv, name='upload_csv'),
    path('download-template/<str:template_type>/', lecturer_views.download_csv_template, name='download_template'),
]
