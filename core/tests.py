from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from core.models import StudentProfile, Company, PlacementDrive, Application
from datetime import date, timedelta

class PlacementSystemComprehensiveTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Admin user
        self.admin = User.objects.create_superuser(
            username='test_admin',
            email='admin@example.com',
            password='Password123!'
        )
        # Student user with StudentProfile
        self.student = User.objects.create_user(
            username='test_student',
            email='student@example.com',
            password='Password123!'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student,
            phone='9876543210',
            department='CSE',
            graduation_year=2025,
            cgpa=8.5,
            backlogs=0
        )
        # Sample Company
        self.company = Company.objects.create(
            name='Test Corp',
            industry='Software',
            location='Bangalore',
            website='https://testcorp.example.com'
        )
        # Sample Drive
        self.drive = PlacementDrive.objects.create(
            company=self.company,
            title='Software Engineer',
            job_description='Develop web apps',
            package_lpa=10.0,
            min_cgpa=7.0,
            max_backlogs=0,
            allowed_departments='CSE,IT',
            target_graduation_year=2025,
            drive_date=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=5),
            status='Active'
        )

    # --- 1. LANDING & PUBLIC ACCESS ---
    def test_landing_page_renders_successfully(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/landing.html')
        self.assertContains(response, 'Connect Students')
        self.assertContains(response, 'Student Login')
        self.assertContains(response, 'Admin')

    # --- 2. ADMIN LOGIN TESTS ---
    def test_admin_login_page_renders(self):
        response = self.client.get(reverse('admin_login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/admin_login.html')
        self.assertContains(response, 'ADMIN ONLY LOGIN')
        self.assertContains(response, 'Placement Drive Management System')

    def test_admin_successful_login_username(self):
        response = self.client.post(reverse('admin_login'), {
            'username': 'test_admin',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_admin_successful_login_email(self):
        response = self.client.post(reverse('admin_login'), {
            'username': 'admin@example.com',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_student_rejected_from_admin_login(self):
        response = self.client.post(reverse('admin_login'), {
            'username': 'test_student',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/admin_login.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('strictly reserved for Administrators' in m.message for m in messages))

    def test_invalid_credentials_on_admin_login(self):
        response = self.client.post(reverse('admin_login'), {
            'username': 'test_admin',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Invalid administrator credentials' in m.message for m in messages))

    # --- 3. STUDENT LOGIN TESTS ---
    def test_student_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')
        self.assertContains(response, 'Admin Login')

    def test_student_successful_login_username(self):
        response = self.client.post(reverse('login'), {
            'username': 'test_student',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_student_successful_login_email(self):
        response = self.client.post(reverse('login'), {
            'username': 'student@example.com',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_student_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'test_student',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Invalid username/email or password' in m.message for m in messages))

    # --- 4. REGISTRATION TESTS ---
    def test_registration_page_renders(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/register.html')

    def test_successful_student_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'new_student',
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'newstudent@example.com',
            'phone': '9998887776',
            'department': 'CSE',
            'graduation_year': 2025,
            'cgpa': 8.0,
            'password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='new_student').exists())
        self.assertTrue(StudentProfile.objects.filter(user__username='new_student').exists())

    # --- 5. LOGOUT TESTS ---
    def test_logout(self):
        self.client.login(username='test_student', password='Password123!')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('landing'))

    # --- 6. DASHBOARDS & PROTECTED PAGES ---
    def test_admin_accesses_admin_dashboard(self):
        self.client.login(username='test_admin', password='Password123!')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/admin_dashboard.html')

    def test_student_accesses_student_dashboard(self):
        self.client.login(username='test_student', password='Password123!')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/student_dashboard.html')

    def test_unauthenticated_user_redirected_from_dashboard(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_companies_list_view(self):
        self.client.login(username='test_admin', password='Password123!')
        response = self.client.get(reverse('company_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Corp')

    def test_drives_list_view(self):
        self.client.login(username='test_student', password='Password123!')
        response = self.client.get(reverse('drive_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Software Engineer')

    # --- 7. CSV EXPORT TESTS ---
    def test_export_applications_csv_admin(self):
        self.client.login(username='test_admin', password='Password123!')
        Application.objects.create(student=self.student_profile, drive=self.drive, status='Pending')
        response = self.client.get(reverse('export_applications_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename="student_applications_', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('Student Name', content)
        self.assertIn('test_student', content)
        self.assertIn('Test Corp', content)
        self.assertIn('Software Engineer', content)

    def test_export_applications_csv_with_filter(self):
        self.client.login(username='test_admin', password='Password123!')
        Application.objects.create(student=self.student_profile, drive=self.drive, status='Selected')
        response = self.client.get(reverse('export_applications_csv') + '?status=Selected')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Selected', content)

    def test_export_applications_csv_denied_for_student(self):
        self.client.login(username='test_student', password='Password123!')
        response = self.client.get(reverse('export_applications_csv'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_export_students_csv_admin(self):
        self.client.login(username='test_admin', password='Password123!')
        response = self.client.get(reverse('export_students_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename="students_list_', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('Full Name', content)
        self.assertIn('test_student', content)
        self.assertIn('CSE', content)

