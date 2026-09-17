from django.db import models
from django.contrib.auth.models import User

DEPARTMENT_CHOICES = [
    ('CSE', 'Computer Science & Engineering'),
    ('IT', 'Information Technology'),
    ('ECE', 'Electronics & Communication Engineering'),
    ('MCA', 'Master of Computer Applications'),
    ('ME', 'Mechanical Engineering'),
    ('CE', 'Civil Engineering'),
    ('OTHER', 'Other / Others'),
]

STATUS_CHOICES = [
    ('Active', 'Active'),
    ('Upcoming', 'Upcoming'),
    ('Closed', 'Closed'),
]

APPLICATION_STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Shortlisted', 'Shortlisted'),
    ('Selected', 'Selected'),
    ('Rejected', 'Rejected'),
]


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    phone = models.CharField(max_length=25, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='Male')
    date_of_birth = models.DateField(null=True, blank=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='CSE')
    college = models.CharField(max_length=100, default='XYZ College')
    graduation_year = models.IntegerField(default=2025)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    backlogs = models.IntegerField(default=0)
    skills = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    linkedin_url = models.URLField(max_length=200, blank=True)
    github_url = models.URLField(max_length=200, blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.department})"


class Company(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    industry = models.CharField(max_length=100, default='IT Services')
    location = models.CharField(max_length=100, default='Bangalore')
    website = models.URLField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=25, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class PlacementDrive(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='drives')
    title = models.CharField(max_length=150)
    job_description = models.TextField()
    package_lpa = models.DecimalField(max_digits=5, decimal_places=2)
    drive_date = models.DateField()
    deadline = models.DateField()
    vacancies = models.IntegerField(default=10)
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=6.0)
    max_backlogs = models.IntegerField(default=0)
    allowed_departments = models.CharField(max_length=200, default="CSE, IT, ECE, MCA")
    required_skills = models.CharField(max_length=255, default="Python, SQL")
    target_graduation_year = models.IntegerField(default=2025)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.name} - {self.title}"


class Application(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name='applications')
    applied_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'drive')

    def __str__(self):
        return f"{self.student.user.username} -> {self.drive.title} ({self.status})"
