from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('submit/', views.submit_complaint, name='submit'),
    path('my/', views.my_complaints, name='my_complaints'),
    path('<int:pk>/', views.complaint_detail, name='detail'),
    path('admin/', views.admin_complaints, name='admin_list'),
    path('admin/<int:pk>/', views.admin_complaint_detail, name='admin_detail'),
]
