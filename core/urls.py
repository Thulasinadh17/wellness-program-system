from django.urls import path
from core.views import (
    home_view, login_view, logout_view, register_view, password_change_view,
    dashboard_redirect,
    # Participant
    participant_dashboard, program_browse_view, program_detail_view,
    program_enroll_view, program_withdraw_view, submit_feedback_view,
    activity_log_view, delete_activity_log, goals_view, toggle_goal_view, notifications_view,
    # Coordinator
    coordinator_dashboard, program_create_view, coordinator_program_detail,
    program_edit_view, program_cancel_view, remove_enrollment_view,
    session_create_view, session_edit_view, mark_attendance_view,
    send_announcement_view, coordinator_reports_view, export_participation_csv,
    # Professional
    professional_dashboard, professional_program_detail,
    # HR
    hr_dashboard,
    # Admin
    admin_dashboard, user_list_view, user_create_view, user_edit_view,
    user_toggle_status, category_list_view, category_create_view,
    category_edit_view, category_delete_view,
)

urlpatterns = [
    # Public & Auth
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('password-change/', password_change_view, name='password_change'),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),

    # Participant Routes
    path('dashboard/participant/', participant_dashboard, name='participant_dashboard'),
    path('programs/', program_browse_view, name='program_browse'),
    path('programs/<int:program_id>/', program_detail_view, name='program_detail'),
    path('programs/<int:program_id>/enroll/', program_enroll_view, name='program_enroll'),
    path('programs/<int:program_id>/withdraw/', program_withdraw_view, name='program_withdraw'),
    path('programs/<int:program_id>/feedback/', submit_feedback_view, name='submit_feedback'),
    path('activity/', activity_log_view, name='activity_log'),
    path('activity/<int:log_id>/delete/', delete_activity_log, name='delete_activity_log'),
    path('goals/', goals_view, name='goals_list'),
    path('goals/<int:goal_id>/toggle/', toggle_goal_view, name='toggle_goal'),
    path('notifications/', notifications_view, name='notifications_inbox'),

    # Coordinator Routes
    path('dashboard/coordinator/', coordinator_dashboard, name='coordinator_dashboard'),
    path('coordinator/programs/create/', program_create_view, name='coordinator_program_create'),
    path('coordinator/programs/<int:program_id>/', coordinator_program_detail, name='coordinator_program_detail'),
    path('coordinator/programs/<int:program_id>/edit/', program_edit_view, name='coordinator_program_edit'),
    path('coordinator/programs/<int:program_id>/cancel/', program_cancel_view, name='coordinator_program_cancel'),
    path('coordinator/programs/<int:program_id>/enrollments/<int:enrollment_id>/remove/', remove_enrollment_view, name='coordinator_remove_enrollment'),
    path('coordinator/programs/<int:program_id>/sessions/create/', session_create_view, name='coordinator_session_create'),
    path('coordinator/programs/<int:program_id>/sessions/<int:session_id>/edit/', session_edit_view, name='coordinator_session_edit'),
    path('coordinator/programs/<int:program_id>/sessions/<int:session_id>/attendance/', mark_attendance_view, name='coordinator_mark_attendance'),
    path('coordinator/programs/<int:program_id>/announce/', send_announcement_view, name='coordinator_send_announcement'),
    path('coordinator/reports/', coordinator_reports_view, name='coordinator_reports'),
    path('coordinator/reports/export-csv/', export_participation_csv, name='coordinator_export_csv'),

    # Professional Routes
    path('dashboard/professional/', professional_dashboard, name='professional_dashboard'),
    path('professional/programs/<int:program_id>/', professional_program_detail, name='professional_program_detail'),

    # HR / Management Routes
    path('dashboard/hr/', hr_dashboard, name='hr_dashboard'),

    # Admin Portal Routes
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('admin-portal/users/', user_list_view, name='admin_user_list'),
    path('admin-portal/users/create/', user_create_view, name='admin_user_create'),
    path('admin-portal/users/<int:user_id>/edit/', user_edit_view, name='admin_user_edit'),
    path('admin-portal/users/<int:user_id>/toggle/', user_toggle_status, name='admin_user_toggle'),
    path('admin-portal/categories/', category_list_view, name='admin_category_list'),
    path('admin-portal/categories/create/', category_create_view, name='admin_category_create'),
    path('admin-portal/categories/<int:category_id>/edit/', category_edit_view, name='admin_category_edit'),
    path('admin-portal/categories/<int:category_id>/delete/', category_delete_view, name='admin_category_delete'),
]
