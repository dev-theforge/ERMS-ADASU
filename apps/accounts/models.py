from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        LECTURER = 'lecturer', _('Lecturer')
        STUDENT = 'student', _('Student')
        PARENT = 'parent', _('Parent/Guardian')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending Approval')
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        REJECTED = 'rejected', _('Rejected')

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin_user(self): return self.role == self.Role.ADMIN
    @property
    def is_lecturer_user(self): return self.role == self.Role.LECTURER
    @property
    def is_student_user(self): return self.role == self.Role.STUDENT
    @property
    def is_parent_user(self): return self.role == self.Role.PARENT
    @property
    def is_active_user(self): return self.status == self.Status.ACTIVE and self.is_active


class Faculty(models.Model):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Faculties'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} — {self.name}"


class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'faculty']

    def __str__(self):
        return f"{self.code} — {self.name}"


class AcademicSession(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text='e.g. 2023/2024')
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicSession.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Semester(models.Model):
    class SemType(models.TextChoices):
        FIRST = 'first', _('First Semester')
        SECOND = 'second', _('Second Semester')

    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='semesters')
    semester_type = models.CharField(max_length=10, choices=SemType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-session__start_date', 'semester_type']
        unique_together = ['session', 'semester_type']

    def __str__(self):
        return f"{self.session.name} — {self.get_semester_type_display()}"

    def save(self, *args, **kwargs):
        if self.is_current:
            Semester.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class GradeScale(models.Model):
    label = models.CharField(max_length=5)
    min_score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    grade_point = models.DecimalField(max_digits=3, decimal_places=1)
    remark = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-min_score']

    def __str__(self):
        return f"{self.label} ({self.min_score}–{self.max_score}) = {self.grade_point}"


class Course(models.Model):
    LEVEL_CHOICES = [(100,'100 Level'),(200,'200 Level'),(300,'300 Level'),(400,'400 Level'),(500,'500 Level')]

    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    credit_units = models.PositiveSmallIntegerField(default=3)
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, default=100)
    semester_type = models.CharField(max_length=10, choices=Semester.SemType.choices, default='first')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.title} ({self.credit_units} units)"


class StudentProfile(models.Model):
    LEVEL_CHOICES = [(100,'100 Level'),(200,'200 Level'),(300,'300 Level'),(400,'400 Level'),(500,'500 Level')]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    matric_number = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='students')
    level = models.IntegerField(choices=LEVEL_CHOICES, default=100)
    admission_year = models.PositiveSmallIntegerField()
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_email = models.EmailField(blank=True)
    state_of_origin = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['matric_number']

    def __str__(self):
        return f"{self.matric_number} — {self.user.get_full_name()}"


class LecturerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='lecturers')
    title = models.CharField(max_length=50, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['staff_id']

    def __str__(self):
        return f"{self.staff_id} — {self.title} {self.user.get_full_name()}".strip()


class CourseAssignment(models.Model):
    lecturer = models.ForeignKey(LecturerProfile, on_delete=models.CASCADE, related_name='course_assignments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='course_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['lecturer', 'course', 'semester']

    def __str__(self):
        return f"{self.lecturer.staff_id} → {self.course.code} ({self.semester})"


class ParentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='parent_profile')
    occupation = models.CharField(max_length=200, blank=True)
    wards = models.ManyToManyField(StudentProfile, blank=True, related_name='parents')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"


class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'course', 'semester']

    def __str__(self):
        return f"{self.student.matric_number} — {self.course.code} ({self.semester})"
