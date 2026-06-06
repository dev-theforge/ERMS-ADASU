"""
Management command: seed initial data for ERMS
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import (
    CustomUser, Faculty, Department, AcademicSession, Semester,
    GradeScale, Course, StudentProfile, LecturerProfile, CourseAssignment, Enrollment
)


class Command(BaseCommand):
    help = 'Seed ERMS with initial data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding ERMS initial data...')

        # Grade Scales
        scales = [
            ('A', 70, 100, 5.0, 'Excellent'),
            ('B', 60, 69, 4.0, 'Very Good'),
            ('C', 50, 59, 3.0, 'Good'),
            ('D', 45, 49, 2.0, 'Pass'),
            ('E', 40, 44, 1.0, 'Marginal Pass'),
            ('F', 0, 39, 0.0, 'Fail'),
        ]
        for label, mn, mx, gp, remark in scales:
            GradeScale.objects.get_or_create(label=label, defaults={'min_score': mn, 'max_score': mx, 'grade_point': gp, 'remark': remark})
        self.stdout.write('  ✓ Grade scales created')

        # Faculty
        fos, _ = Faculty.objects.get_or_create(name='Faculty of Science', code='FOS')
        fss, _ = Faculty.objects.get_or_create(name='Faculty of Social Sciences', code='FSS')
        foe, _ = Faculty.objects.get_or_create(name='Faculty of Engineering', code='FOE')

        # Departments
        csc, _ = Department.objects.get_or_create(name='Computer Science', code='CSC', defaults={'faculty': fos})
        mth, _ = Department.objects.get_or_create(name='Mathematics', code='MTH', defaults={'faculty': fos})
        eco, _ = Department.objects.get_or_create(name='Economics', code='ECO', defaults={'faculty': fss})
        self.stdout.write('  ✓ Faculties and departments created')

        # Academic Session
        session, _ = AcademicSession.objects.get_or_create(
            name='2023/2024',
            defaults={'start_date': '2023-09-01', 'end_date': '2024-07-31', 'is_current': True}
        )
        sem1, _ = Semester.objects.get_or_create(
            session=session, semester_type='first',
            defaults={'start_date': '2023-09-01', 'end_date': '2024-01-31', 'is_current': True}
        )
        sem2, _ = Semester.objects.get_or_create(
            session=session, semester_type='second',
            defaults={'start_date': '2024-02-01', 'end_date': '2024-07-31'}
        )
        self.stdout.write('  ✓ Academic session and semesters created')

        # Courses
        csc101, _ = Course.objects.get_or_create(code='CSC101', defaults={'title': 'Introduction to Computing', 'department': csc, 'credit_units': 3, 'level': 100, 'semester_type': 'first'})
        csc201, _ = Course.objects.get_or_create(code='CSC201', defaults={'title': 'Data Structures', 'department': csc, 'credit_units': 3, 'level': 200, 'semester_type': 'first'})
        mth101, _ = Course.objects.get_or_create(code='MTH101', defaults={'title': 'Calculus I', 'department': mth, 'credit_units': 3, 'level': 100, 'semester_type': 'first'})
        mth201, _ = Course.objects.get_or_create(code='MTH201', defaults={'title': 'Linear Algebra', 'department': mth, 'credit_units': 3, 'level': 200, 'semester_type': 'second'})
        self.stdout.write('  ✓ Courses created')

        # Admin user
        if not CustomUser.objects.filter(username='admin').exists():
            admin = CustomUser.objects.create_superuser('admin', 'admin@adasu.edu.ng', 'Admin@1234')
            admin.role = 'admin'
            admin.status = 'active'
            admin.first_name = 'System'
            admin.last_name = 'Administrator'
            admin.save()
            self.stdout.write('  ✓ Admin user created (admin / Admin@1234)')

        # Lecturer
        if not CustomUser.objects.filter(username='lec001').exists():
            lec_user = CustomUser.objects.create_user('lec001', 'lec001@adasu.edu.ng', 'Lec@12345')
            lec_user.role = 'lecturer'
            lec_user.status = 'active'
            lec_user.first_name = 'Dr. Emmanuel'
            lec_user.last_name = 'Okwu'
            lec_user.save()
            lec = LecturerProfile.objects.create(user=lec_user, staff_id='ADU/LEC/001', department=csc, title='Dr.')
            CourseAssignment.objects.get_or_create(lecturer=lec, course=csc101, semester=sem1)
            CourseAssignment.objects.get_or_create(lecturer=lec, course=csc201, semester=sem1)
            self.stdout.write('  ✓ Lecturer created (lec001 / Lec@12345)')

        # Students
        for i in range(1, 4):
            uname = f'stu{i:03d}'
            matric = f'ADU/2023/{i:04d}'
            if not CustomUser.objects.filter(username=uname).exists():
                s_user = CustomUser.objects.create_user(uname, f'{uname}@student.adasu.edu.ng', 'Stu@12345')
                s_user.role = 'student'
                s_user.status = 'active'
                s_user.first_name = f'Student{i}'
                s_user.last_name = 'Testuser'
                s_user.save()
                sp = StudentProfile.objects.create(user=s_user, matric_number=matric, department=csc, level=100, admission_year=2023)
                Enrollment.objects.get_or_create(student=sp, course=csc101, semester=sem1)
                Enrollment.objects.get_or_create(student=sp, course=mth101, semester=sem1)
        self.stdout.write(f'  ✓ 3 student accounts created (stu001-stu003 / Stu@12345)')

        # Parent
        if not CustomUser.objects.filter(username='parent01').exists():
            from apps.accounts.models import ParentProfile
            p_user = CustomUser.objects.create_user('parent01', 'parent01@email.com', 'Parent@1234')
            p_user.role = 'parent'
            p_user.status = 'active'
            p_user.first_name = 'Mrs. Grace'
            p_user.last_name = 'Testparent'
            p_user.save()
            parent = ParentProfile.objects.create(user=p_user)
            stu = StudentProfile.objects.filter(matric_number='ADU/2023/0001').first()
            if stu:
                parent.wards.add(stu)
            self.stdout.write('  ✓ Parent created (parent01 / Parent@1234)')

        self.stdout.write(self.style.SUCCESS('\n✅ ERMS seed data complete!\n'))
        self.stdout.write('Login credentials:')
        self.stdout.write('  Admin:   admin    / Admin@1234')
        self.stdout.write('  Lecturer: lec001  / Lec@12345')
        self.stdout.write('  Student:  stu001  / Stu@12345')
        self.stdout.write('  Parent:   parent01 / Parent@1234')
