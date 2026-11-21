from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Category, Program, Session, Enrollment, Attendance,
    ActivityLog, Goal, Notification, Feedback, ProgressNote
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'points', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff', 'department')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'department')
    fieldsets = UserAdmin.fieldsets + (
        ('Wellness Profile', {'fields': ('role', 'phone_number', 'department', 'professional_title', 'points', 'bio')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Wellness Profile', {'fields': ('role', 'phone_number', 'department', 'professional_title')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color', 'created_at')
    search_fields = ('name',)


class SessionInline(admin.TabularInline):
    model = Session
    extra = 1


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'coordinator', 'assigned_professional', 'start_date', 'end_date', 'capacity', 'status')
    list_filter = ('status', 'category', 'coordinator')
    search_fields = ('title', 'description')
    inlines = [SessionInline]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'program', 'session_date', 'start_time', 'end_time', 'location', 'is_completed')
    list_filter = ('is_completed', 'session_date', 'program')
    search_fields = ('title', 'program__title')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'status', 'enrolled_at', 'participation_rate', 'is_eligible_for_reward')
    list_filter = ('status', 'program')
    search_fields = ('user__username', 'program__title')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('session', 'enrollment', 'attended', 'marked_by', 'marked_at')
    list_filter = ('attended', 'session__program')
    search_fields = ('enrollment__user__username', 'session__title')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'log_date', 'steps', 'workout_minutes', 'water_intake_ml', 'sleep_hours')
    list_filter = ('log_date',)
    search_fields = ('user__username',)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'goal_type', 'target_value', 'unit', 'is_achieved', 'target_date')
    list_filter = ('goal_type', 'is_achieved')
    search_fields = ('user__username', 'title')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('user__username', 'title')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('program', 'participant', 'rating', 'submitted_at')
    list_filter = ('rating', 'program')
    search_fields = ('participant__username', 'program__title', 'comments')


@admin.register(ProgressNote)
class ProgressNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'program', 'professional', 'participant', 'note_type', 'created_at')
    list_filter = ('note_type', 'program', 'professional')
    search_fields = ('title', 'content', 'program__title')
