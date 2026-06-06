from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('submit/', views.submit_feedback, name='submit'),
    path('report/', views.feedback_report, name='report'),
]
