from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_home, name='home'),
    path('student/', views.student_report, name='student'),
    path('department/', views.department_report, name='department'),
    path('course/', views.course_report, name='course'),
    path('gpa-distribution/', views.gpa_distribution_report, name='gpa_distribution'),
]
