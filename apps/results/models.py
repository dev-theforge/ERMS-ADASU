from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import StudentProfile, LecturerProfile, Course, Semester, GradeScale


class Result(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SUBMITTED = 'submitted', _('Submitted for Approval')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        PUBLISHED = 'published', _('Published')

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='results')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='results')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='results')
    lecturer = models.ForeignKey(LecturerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_results')
    score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade = models.CharField(max_length=5, blank=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    quality_points = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_results')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'course', 'semester']
        ordering = ['-semester__session__start_date', 'course__code']

    def __str__(self):
        return f"{self.student.matric_number} — {self.course.code}: {self.score}"

    def compute_grade(self):
        scale = GradeScale.objects.filter(
            min_score__lte=self.score, max_score__gte=self.score, is_active=True
        ).first()
        if scale:
            self.grade = scale.label
            self.grade_point = scale.grade_point
        else:
            self.grade = 'F'
            self.grade_point = 0.0
        self.quality_points = float(self.grade_point) * self.course.credit_units

    def save(self, *args, **kwargs):
        self.compute_grade()
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def can_edit(self):
        return self.status in [self.Status.DRAFT, self.Status.REJECTED]


class SemesterGPA(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='semester_gpas')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='gpas')
    total_credit_units = models.PositiveSmallIntegerField(default=0)
    total_quality_points = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'semester']
        ordering = ['-semester__session__start_date']

    def __str__(self):
        return f"{self.student.matric_number} {self.semester}: GPA={self.gpa}"

    def compute(self):
        results = Result.objects.filter(student=self.student, semester=self.semester, status=Result.Status.PUBLISHED)
        self.total_credit_units = sum(r.course.credit_units for r in results)
        self.total_quality_points = sum(float(r.quality_points) for r in results)
        self.gpa = round(self.total_quality_points / self.total_credit_units, 2) if self.total_credit_units else 0


class StudentCGPA(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='cgpa_record')
    total_accumulated_credit_units = models.PositiveIntegerField(default=0)
    total_accumulated_quality_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    computed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.matric_number} CGPA: {self.cgpa}"

    def compute(self):
        results = Result.objects.filter(student=self.student, status=Result.Status.PUBLISHED)
        self.total_accumulated_credit_units = sum(r.course.credit_units for r in results)
        self.total_accumulated_quality_points = sum(float(r.quality_points) for r in results)
        self.cgpa = round(float(self.total_accumulated_quality_points) / self.total_accumulated_credit_units, 2) if self.total_accumulated_credit_units else 0


class ResultUploadLog(models.Model):
    lecturer = models.ForeignKey(LecturerProfile, on_delete=models.CASCADE, related_name='upload_logs')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    total_rows = models.PositiveIntegerField(default=0)
    successful_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Upload by {self.lecturer.staff_id} on {self.uploaded_at:%Y-%m-%d} ({self.successful_rows}/{self.total_rows})"
