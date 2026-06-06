from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (CustomUser, Faculty, Department, AcademicSession, Semester,
                     GradeScale, Course, StudentProfile, LecturerProfile,
                     CourseAssignment, ParentProfile, Enrollment)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'email', 'role', 'status', 'date_joined']
    list_filter = ['role', 'status', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    fieldsets = UserAdmin.fieldsets + (
        ('ERMS Info', {'fields': ('role', 'status', 'phone_number', 'profile_picture', 'date_of_birth', 'address')}),
    )


admin.site.register(Faculty)
admin.site.register(Department)
admin.site.register(AcademicSession)
admin.site.register(Semester)
admin.site.register(GradeScale)
admin.site.register(Course)
admin.site.register(StudentProfile)
admin.site.register(LecturerProfile)
admin.site.register(CourseAssignment)
admin.site.register(ParentProfile)
admin.site.register(Enrollment)
