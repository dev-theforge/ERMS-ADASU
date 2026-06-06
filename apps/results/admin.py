from django.contrib import admin
from .models import Result, SemesterGPA, StudentCGPA, ResultUploadLog

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'semester', 'score', 'grade', 'status', 'lecturer']
    list_filter = ['status', 'semester', 'grade']
    search_fields = ['student__matric_number', 'course__code']

admin.site.register(SemesterGPA)
admin.site.register(StudentCGPA)
admin.site.register(ResultUploadLog)
