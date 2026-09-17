from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile, Company, PlacementDrive, Application


class StudentRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter your username'
    }))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Last Name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter your email address'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter your password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm your password'
    }))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter your phone number'
    }))
    department = forms.ChoiceField(choices=StudentProfile._meta.get_field('department').choices, widget=forms.Select(attrs={
        'class': 'form-select'
    }))
    graduation_year = forms.IntegerField(initial=2025, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'placeholder': 'e.g., 2025'
    }))
    cgpa = forms.DecimalField(max_digits=4, decimal_places=2, initial=0.0, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g., 8.5'
    }))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match!")
        return cleaned_data


class StudentProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = StudentProfile
        fields = [
            'phone', 'gender', 'date_of_birth', 'department', 'college',
            'graduation_year', 'cgpa', 'backlogs', 'skills', 'certifications',
            'projects', 'linkedin_url', 'github_url', 'resume'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'college': forms.TextInput(attrs={'class': 'form-control'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'cgpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'backlogs': forms.NumberInput(attrs={'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Python, SQL, HTML, CSS'}),
            'certifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'projects': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/...'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/...'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'logo', 'industry', 'location', 'website', 'description', 'contact_person', 'contact_email', 'contact_phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. IT Services'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Bangalore'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description...'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@company.com'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Phone'}),
        }


class PlacementDriveForm(forms.ModelForm):
    class Meta:
        model = PlacementDrive
        fields = [
            'company', 'title', 'job_description', 'package_lpa', 'drive_date', 'deadline',
            'vacancies', 'min_cgpa', 'max_backlogs', 'allowed_departments', 'required_skills',
            'target_graduation_year', 'status'
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Python Developer'}),
            'job_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'package_lpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'e.g., 6.5'}),
            'drive_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vacancies': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_cgpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_backlogs': forms.NumberInput(attrs={'class': 'form-control'}),
            'allowed_departments': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CSE, IT, ECE, MCA'}),
            'required_skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Python, SQL, React'}),
            'target_graduation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status', 'remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional feedback/remarks...'}),
        }
