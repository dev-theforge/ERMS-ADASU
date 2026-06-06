from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/lecturer/', views.register_lecturer, name='register_lecturer'),
    path('register/parent/', views.register_parent, name='register_parent'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
]
