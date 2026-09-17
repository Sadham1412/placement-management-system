from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('adminlogin/', views.admin_login_view, name='admin_login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('students/', views.student_list_view, name='student_list'),
    path('students/profile/', views.student_profile_view, name='my_profile'),
    path('students/profile/<int:pk>/', views.student_profile_view, name='student_profile_pk'),
    path('students/edit/', views.edit_student_view, name='edit_profile'),
    path('students/edit/<int:pk>/', views.edit_student_view, name='edit_student'),
    path('students/delete/<int:pk>/', views.delete_student_view, name='delete_student'),
    path('students/export-csv/', views.export_students_csv, name='export_students_csv'),

    path('companies/', views.company_list_view, name='company_list'),
    path('companies/add/', views.add_company_view, name='add_company'),
    path('companies/edit/<int:pk>/', views.edit_company_view, name='edit_company'),
    path('companies/delete/<int:pk>/', views.delete_company_view, name='delete_company'),

    path('drives/', views.drive_list_view, name='drive_list'),
    path('drives/add/', views.add_drive_view, name='add_drive'),
    path('drives/<int:drive_id>/eligibility/', views.check_eligibility_view, name='check_eligibility'),
    path('drives/<int:drive_id>/apply/', views.apply_drive_view, name='apply_drive'),
    path('drives/<int:pk>/edit/', views.edit_drive_view, name='edit_drive'),
    path('drives/<int:pk>/delete/', views.delete_drive_view, name='delete_drive'),
    path('drives/<int:pk>/', views.drive_detail_view, name='drive_detail'),

    path('applications/', views.application_list_view, name='application_list'),
    path('applications/export-csv/', views.export_applications_csv, name='export_applications_csv'),
    path('applications/my/', views.my_applications_view, name='my_applications'),
    path('applications/update-status/<int:pk>/', views.update_application_status_view, name='update_application_status'),
]
