import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from .models import StudentProfile, Company, PlacementDrive, Application
from .forms import (
    StudentRegistrationForm, StudentProfileForm,
    CompanyForm, PlacementDriveForm
)


# simple helper - returns True if the logged-in user is admin or staff
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# -------------------------------------------------------
# HOME / AUTH VIEWS
# -------------------------------------------------------

def landing_view(request):
    # show latest 4 active drives and some quick stats on the home page
    drives = PlacementDrive.objects.filter(status='Active').order_by('-created_at')[:4]
    total_students = StudentProfile.objects.count()
    total_companies = Company.objects.count()
    total_drives = PlacementDrive.objects.count()

    context = {
        'drives': drives,
        'total_students': total_students,
        'total_companies': total_companies,
        'total_drives': total_drives,
    }
    return render(request, 'dashboard/landing.html', context)


def login_view(request):
    # redirect if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # allow login with email address as well as username
        username = username_or_email
        if '@' in username_or_email:
            matched_user = User.objects.filter(email__iexact=username_or_email).first()
            if matched_user:
                username = matched_user.username

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            if next_url and next_url != 'None':
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username/email or password.")
            form = AuthenticationForm(request)
    else:
        form = AuthenticationForm()

    return render(request, 'auth/login.html', {'form': form, 'next_url': next_url})


def admin_login_view(request):
    # if already logged in, send to dashboard
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard')
        else:
            messages.info(request, "You are currently signed in with a student account.")
            return redirect('dashboard')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # support email login for admin as well
        username = username_or_email
        if '@' in username_or_email:
            matched_user = User.objects.filter(email__iexact=username_or_email).first()
            if matched_user:
                username = matched_user.username

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f"Welcome Administrator, {user.first_name or user.username}!")
                if next_url and next_url != 'None':
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                # block students from using this admin login portal
                messages.error(
                    request,
                    "Access denied: This login portal is strictly reserved for Administrators."
                )
                form = AuthenticationForm(request)
        else:
            messages.error(request, "Invalid administrator credentials.")
            form = AuthenticationForm(request)
    else:
        form = AuthenticationForm()

    return render(request, 'auth/admin_login.html', {'form': form, 'next_url': next_url})


def register_view(request):
    # already logged in? no need to register again
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            # create the user account first
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # then create the student profile linked to that user
            StudentProfile.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                department=form.cleaned_data['department'],
                graduation_year=form.cleaned_data['graduation_year'],
                cgpa=form.cleaned_data['cgpa']
            )

            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors in the registration form.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('landing')


# -------------------------------------------------------
# DASHBOARD
# -------------------------------------------------------

@login_required
def dashboard_view(request):
    if is_admin(request.user):
        # admin sees overall stats
        total_students = StudentProfile.objects.count()
        total_companies = Company.objects.count()
        total_drives = PlacementDrive.objects.count()
        total_applications = Application.objects.count()
        shortlisted_count = Application.objects.filter(status='Shortlisted').count()
        selected_count = Application.objects.filter(status='Selected').count()
        rejected_count = Application.objects.filter(status='Rejected').count()
        pending_count = Application.objects.filter(status='Pending').count()
        recent_drives = PlacementDrive.objects.order_by('-created_at')[:5]

        context = {
            'total_students': total_students,
            'total_companies': total_companies,
            'total_drives': total_drives,
            'total_applications': total_applications,
            'shortlisted_count': shortlisted_count,
            'selected_count': selected_count,
            'rejected_count': rejected_count,
            'pending_count': pending_count,
            'recent_drives': recent_drives,
        }
        return render(request, 'dashboard/admin_dashboard.html', context)

    else:
        # student sees their own stats
        try:
            profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            # create a blank profile if it doesn't exist yet
            profile = StudentProfile.objects.create(user=request.user)

        available_drives = PlacementDrive.objects.filter(status='Active')

        # count how many active drives this student qualifies for
        eligible_drives_count = 0
        for drive in available_drives:
            dept_list = [d.strip() for d in drive.allowed_departments.split(',')]
            if (profile.cgpa >= drive.min_cgpa and
                profile.backlogs <= drive.max_backlogs and
                (profile.department in dept_list or 'ALL' in drive.allowed_departments.upper()) and
                profile.graduation_year == drive.target_graduation_year):
                eligible_drives_count += 1

        applied_drives_count = Application.objects.filter(student=profile).count()
        shortlisted_count = Application.objects.filter(student=profile, status='Shortlisted').count()
        selected_count = Application.objects.filter(student=profile, status='Selected').count()
        rejected_count = Application.objects.filter(student=profile, status='Rejected').count()
        pending_count = Application.objects.filter(student=profile, status='Pending').count()
        recent_drives = PlacementDrive.objects.filter(status='Active').order_by('-created_at')[:4]

        context = {
            'profile': profile,
            'available_drives_count': available_drives.count(),
            'eligible_drives_count': eligible_drives_count,
            'applied_drives_count': applied_drives_count,
            'shortlisted_count': shortlisted_count,
            'selected_count': selected_count,
            'rejected_count': rejected_count,
            'pending_count': pending_count,
            'recent_drives': recent_drives,
        }
        return render(request, 'dashboard/student_dashboard.html', context)


# -------------------------------------------------------
# STUDENTS
# -------------------------------------------------------

@login_required
def student_list_view(request):
    # only admins can see the full student directory
    if not is_admin(request.user):
        messages.error(request, "Access denied. Admins only.")
        return redirect('dashboard')

    students = StudentProfile.objects.select_related('user').all()

    # search by name, username, or email
    search_query = request.GET.get('q', '').strip()
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    # filter by department
    dept_filter = request.GET.get('department', '')
    if dept_filter:
        students = students.filter(department=dept_filter)

    # filter by minimum CGPA
    min_cgpa = request.GET.get('min_cgpa', '')
    if min_cgpa:
        try:
            students = students.filter(cgpa__gte=float(min_cgpa))
        except ValueError:
            pass

    context = {
        'students': students,
        'search_query': search_query,
        'dept_filter': dept_filter,
        'min_cgpa': min_cgpa,
    }
    return render(request, 'students/student_list.html', context)


@login_required
def export_students_csv(request):
    # only admins can download student data
    if not is_admin(request.user):
        messages.error(request, "Access denied. Admins only.")
        return redirect('dashboard')

    students = StudentProfile.objects.select_related('user').all().order_by('user__first_name')

    # if ?all=1 is passed, skip filters and export everything
    export_all = request.GET.get('all') == '1'
    if not export_all:
        search_query = request.GET.get('q', '').strip()
        if search_query:
            students = students.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )

        dept_filter = request.GET.get('department', '')
        if dept_filter:
            students = students.filter(department=dept_filter)

        min_cgpa = request.GET.get('min_cgpa', '')
        if min_cgpa:
            try:
                students = students.filter(cgpa__gte=float(min_cgpa))
            except ValueError:
                pass

    # build the CSV response
    filename = f"students_list_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'Full Name', 'Username / Roll No', 'Email', 'Phone',
        'Gender', 'Department', 'College', 'Graduation Year', 'CGPA',
        'Backlogs', 'Skills', 'LinkedIn Profile', 'GitHub Profile', 'Date Registered'
    ])

    for s in students:
        u = s.user
        writer.writerow([
            s.id, u.get_full_name() or u.username, u.username, u.email,
            s.phone or 'N/A', s.gender, s.department, s.college,
            s.graduation_year, s.cgpa, s.backlogs, s.skills or 'N/A',
            s.linkedin_url or 'N/A', s.github_url or 'N/A',
            u.date_joined.strftime('%Y-%m-%d %H:%M:%S') if u.date_joined else ''
        ])

    return response


@login_required
def student_profile_view(request, pk=None):
    # admin can view any student profile; students see their own
    if pk and is_admin(request.user):
        profile = get_object_or_404(StudentProfile, pk=pk)
    else:
        profile = get_object_or_404(StudentProfile, user=request.user)

    context = {
        'profile': profile,
        'skills_list': [s.strip() for s in profile.skills.split(',')] if profile.skills else []
    }
    return render(request, 'students/student_profile.html', context)


@login_required
def edit_student_view(request, pk=None):
    # admin can edit any student; students can only edit themselves
    if pk and is_admin(request.user):
        profile = get_object_or_404(StudentProfile, pk=pk)
    else:
        profile = get_object_or_404(StudentProfile, user=request.user)

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()

            # also update the user's name and email fields
            user = profile.user
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.save()

            messages.success(request, "Profile updated successfully!")
            return redirect('student_profile_pk', pk=profile.pk) if is_admin(request.user) else redirect('my_profile')
    else:
        # pre-fill user fields into the form
        initial_data = {
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'email': profile.user.email,
        }
        form = StudentProfileForm(instance=profile, initial=initial_data)

    return render(request, 'students/student_form.html', {'form': form, 'profile': profile})


@login_required
def delete_student_view(request, pk):
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    profile = get_object_or_404(StudentProfile, pk=pk)
    user = profile.user
    user.delete()  # deleting the user also deletes the profile (CASCADE)
    messages.success(request, "Student account deleted successfully.")
    return redirect('student_list')


# -------------------------------------------------------
# COMPANIES
# -------------------------------------------------------

@login_required
def company_list_view(request):
    # annotate with how many drives each company has posted
    companies = Company.objects.annotate(drives_count=Count('drives')).all()

    search_query = request.GET.get('q', '').strip()
    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query) |
            Q(industry__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    context = {
        'companies': companies,
        'search_query': search_query,
    }
    return render(request, 'companies/company_list.html', context)


@login_required
def add_company_view(request):
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('company_list')

    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Company added successfully!")
            return redirect('company_list')
    else:
        form = CompanyForm()

    return render(request, 'companies/company_form.html', {'form': form, 'title': 'Add Company'})


@login_required
def edit_company_view(request, pk):
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('company_list')

    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company updated successfully!")
            return redirect('company_list')
    else:
        form = CompanyForm(instance=company)

    return render(request, 'companies/company_form.html', {'form': form, 'title': 'Edit Company', 'company': company})


@login_required
def delete_company_view(request, pk):
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('company_list')

    company = get_object_or_404(Company, pk=pk)
    company.delete()
    messages.success(request, "Company deleted successfully.")
    return redirect('company_list')


# -------------------------------------------------------
# PLACEMENT DRIVES
# -------------------------------------------------------

@login_required
def drive_list_view(request):
    drives = PlacementDrive.objects.select_related('company').all().order_by('-created_at')

    # search by title or company name
    search_query = request.GET.get('q', '').strip()
    if search_query:
        drives = drives.filter(
            Q(title__icontains=search_query) |
            Q(company__name__icontains=search_query)
        )

    # filter by drive status (Active / Upcoming / Closed)
    status_filter = request.GET.get('status', '')
    if status_filter:
        drives = drives.filter(status=status_filter)

    context = {
        'drives': drives,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'drives/drive_list.html', context)


@login_required
def add_drive_view(request):
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('drive_list')

    if request.method == 'POST':
        form = PlacementDriveForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Placement drive created successfully!")
            return redirect('drive_list')
    else:
        form = PlacementDriveForm()

    return render(request, 'drives/drive_form.html', {'form': form, 'title': 'Add Placement Drive'})


@login_required
def edit_drive_view(request, pk):
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('drive_list')

    drive = get_object_or_404(PlacementDrive, pk=pk)
    if request.method == 'POST':
        form = PlacementDriveForm(request.POST, instance=drive)
        if form.is_valid():
            form.save()
            messages.success(request, "Placement drive updated successfully!")
            return redirect('drive_list')
    else:
        form = PlacementDriveForm(instance=drive)

    return render(request, 'drives/drive_form.html', {'form': form, 'title': 'Edit Placement Drive', 'drive': drive})


@login_required
def delete_drive_view(request, pk):
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('drive_list')

    drive = get_object_or_404(PlacementDrive, pk=pk)
    drive.delete()
    messages.success(request, "Placement drive deleted successfully.")
    return redirect('drive_list')


@login_required
def drive_detail_view(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    already_applied = False
    application = None

    # check if the logged-in student has already applied to this drive
    if hasattr(request.user, 'student_profile'):
        application = Application.objects.filter(
            student=request.user.student_profile, drive=drive
        ).first()
        already_applied = application is not None

    context = {
        'drive': drive,
        'already_applied': already_applied,
        'application': application,
        'departments_list': [d.strip() for d in drive.allowed_departments.split(',')]
    }
    return render(request, 'drives/drive_detail.html', context)


# -------------------------------------------------------
# ELIGIBILITY & APPLICATIONS
# -------------------------------------------------------

@login_required
def check_eligibility_view(request, drive_id):
    drive = get_object_or_404(PlacementDrive, pk=drive_id)

    # only students can check eligibility
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can check eligibility for drives.")
        return redirect('drive_detail', pk=drive_id)

    student = request.user.student_profile
    already_applied = Application.objects.filter(student=student, drive=drive).exists()

    # run the 5 eligibility checks
    cgpa_pass = student.cgpa >= drive.min_cgpa
    backlog_pass = student.backlogs <= drive.max_backlogs
    dept_list = [d.strip().upper() for d in drive.allowed_departments.split(',')]
    dept_pass = student.department.upper() in dept_list or 'ALL' in dept_list
    grad_pass = student.graduation_year == drive.target_graduation_year

    req_skills_list = [s.strip().lower() for s in (drive.required_skills or '').split(',') if s.strip()]
    user_skills_list = [s.strip().lower() for s in (student.skills or '').split(',') if s.strip()]

    if req_skills_list:
        matched_skills = [s for s in req_skills_list if any(us in s or s in us for us in user_skills_list)]
        skills_pass = len(matched_skills) > 0
    else:
        matched_skills = []
        skills_pass = True

    is_eligible = cgpa_pass and backlog_pass and dept_pass and grad_pass and skills_pass

    context = {
        'drive': drive,
        'student': student,
        'cgpa_pass': cgpa_pass,
        'backlog_pass': backlog_pass,
        'dept_pass': dept_pass,
        'grad_pass': grad_pass,
        'skills_pass': skills_pass,
        'matched_skills': matched_skills,
        'req_skills_list': [s.strip() for s in (drive.required_skills or '').split(',') if s.strip()],
        'is_eligible': is_eligible,
        'already_applied': already_applied,
    }
    return render(request, 'applications/eligibility_check.html', context)


@login_required
def apply_drive_view(request, drive_id):
    drive = get_object_or_404(PlacementDrive, pk=drive_id)

    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can apply to drives.")
        return redirect('drive_detail', pk=drive_id)

    student = request.user.student_profile

    # re-check eligibility before saving the application (security measure)
    dept_list = [d.strip().upper() for d in drive.allowed_departments.split(',')]
    req_skills_list = [s.strip().lower() for s in (drive.required_skills or '').split(',') if s.strip()]
    user_skills_list = [s.strip().lower() for s in (student.skills or '').split(',') if s.strip()]
    skills_pass = True if not req_skills_list else (
        any(s in us or us in s for s in req_skills_list for us in user_skills_list) and len(user_skills_list) > 0
    )

    is_eligible = (
        student.cgpa >= drive.min_cgpa and
        student.backlogs <= drive.max_backlogs and
        (student.department.upper() in dept_list or 'ALL' in dept_list) and
        student.graduation_year == drive.target_graduation_year and
        skills_pass
    )

    if not is_eligible:
        messages.error(request, "You are not eligible for this placement drive.")
        return redirect('check_eligibility', drive_id=drive_id)

    # get_or_create prevents duplicate applications
    app, created = Application.objects.get_or_create(student=student, drive=drive)
    if created:
        messages.success(request, f"Application submitted successfully for {drive.title} at {drive.company.name}!")
    else:
        messages.info(request, "You have already applied for this placement drive.")

    return redirect('my_applications')


@login_required
def application_list_view(request):
    # only admins can track all applications
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    applications = Application.objects.select_related(
        'student__user', 'drive__company'
    ).all().order_by('-applied_date')

    # filter by company
    company_id = request.GET.get('company', '')
    if company_id:
        applications = applications.filter(drive__company_id=company_id)

    # filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = applications.filter(status=status_filter)

    # search by student name, drive title, or company
    search_query = request.GET.get('q', '').strip()
    if search_query:
        applications = applications.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(drive__title__icontains=search_query) |
            Q(drive__company__name__icontains=search_query)
        )

    companies = Company.objects.all()

    context = {
        'applications': applications,
        'companies': companies,
        'company_id': company_id,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'applications/application_list.html', context)


@login_required
def export_applications_csv(request):
    # only admins can download application data
    if not is_admin(request.user):
        messages.error(request, "Access denied. Admins only.")
        return redirect('dashboard')

    applications = Application.objects.select_related(
        'student__user', 'drive__company'
    ).all().order_by('-applied_date')

    # ?all=1 exports everything without filters
    export_all = request.GET.get('all') == '1'
    if not export_all:
        company_id = request.GET.get('company', '')
        if company_id:
            applications = applications.filter(drive__company_id=company_id)

        status_filter = request.GET.get('status', '')
        if status_filter:
            applications = applications.filter(status=status_filter)

        search_query = request.GET.get('q', '').strip()
        if search_query:
            applications = applications.filter(
                Q(student__user__first_name__icontains=search_query) |
                Q(student__user__last_name__icontains=search_query) |
                Q(student__user__username__icontains=search_query) |
                Q(drive__title__icontains=search_query) |
                Q(drive__company__name__icontains=search_query)
            )

    filename = f"student_applications_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Application ID', 'Student Name', 'Username / Roll No', 'Email', 'Phone',
        'Department', 'College', 'Graduation Year', 'CGPA', 'Backlogs',
        'Skills', 'Company', 'Job Role', 'Package (LPA)', 'Applied Date', 'Status', 'Remarks'
    ])

    for app in applications:
        s = app.student
        u = s.user
        d = app.drive
        writer.writerow([
            app.id, u.get_full_name() or u.username, u.username, u.email,
            s.phone or 'N/A', s.department, s.college, s.graduation_year,
            s.cgpa, s.backlogs, s.skills or 'N/A', d.company.name,
            d.title, d.package_lpa,
            app.applied_date.strftime('%Y-%m-%d %H:%M:%S') if app.applied_date else '',
            app.status, app.remarks or ''
        ])

    return response


@login_required
def my_applications_view(request):
    # students can only see their own applications here
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    student = request.user.student_profile
    applications = Application.objects.select_related(
        'drive__company'
    ).filter(student=student).order_by('-applied_date')

    context = {
        'applications': applications
    }
    return render(request, 'applications/my_applications.html', context)


@login_required
def update_application_status_view(request, pk):
    if not is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    application = get_object_or_404(Application, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')

        # make sure the status value is one of the valid choices
        if new_status in dict(Application._meta.get_field('status').choices):
            application.status = new_status
            application.remarks = remarks
            application.save()
            messages.success(
                request,
                f"Application status updated to '{new_status}' for {application.student.user.get_full_name()}."
            )

    return redirect('application_list')
