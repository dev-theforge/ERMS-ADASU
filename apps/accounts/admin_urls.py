from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.admin_users, name='users'),
    path('users/<int:pk>/action/', views.admin_approve_user, name='user_action'),
    path('faculties/', views.admin_faculties, name='faculties'),
    path('departments/', views.admin_departments, name='departments'),
    path('sessions/', views.admin_sessions, name='sessions'),
    path('semesters/', views.admin_semesters, name='semesters'),
    path('courses/', views.admin_courses, name='courses'),
    path('grade-scales/', views.admin_grade_scales, name='grade_scales'),
    path('audit-logs/', views.admin_audit_logs, name='audit_logs'),
    path('publish-results/', views.admin_publish_results, name='publish_results'),
    path('approve-results/', views.admin_approve_results, name='approve_results'),
]
