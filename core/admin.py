from django.contrib import admin
from .models import StudentProfile, Company, PlacementDrive, Application

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'graduation_year', 'cgpa', 'backlogs', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'department')
    list_filter = ('department', 'graduation_year')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'location', 'website', 'contact_person', 'created_at')
    search_fields = ('name', 'industry', 'location')
    list_filter = ('industry', 'location')

@admin.register(PlacementDrive)
class PlacementDriveAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'package_lpa', 'drive_date', 'deadline', 'status', 'min_cgpa')
    search_fields = ('title', 'company__name')
    list_filter = ('status', 'company')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'drive', 'status', 'applied_date')
    search_fields = ('student__user__username', 'drive__title', 'drive__company__name')
    list_filter = ('status', 'applied_date')
