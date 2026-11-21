from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        PARTICIPANT = 'PARTICIPANT', 'Participant'
        COORDINATOR = 'COORDINATOR', 'Wellness Coordinator'
        PROFESSIONAL = 'PROFESSIONAL', 'Wellness Professional'
        HR = 'HR', 'HR / Management'
        ADMIN = 'ADMIN', 'Administrator'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PARTICIPANT,
        help_text="Role determining access permissions in the wellness portal"
    )
    phone_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True, help_text="e.g. Engineering, Sales, Faculty")
    professional_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. Certified Personal Trainer, Clinical Nutritionist"
    )
    points = models.PositiveIntegerField(default=0, help_text="Reward points accumulated")
    bio = models.TextField(blank=True)

    def is_participant(self):
        return self.role == self.Role.PARTICIPANT

    def is_coordinator(self):
        return self.role == self.Role.COORDINATOR

    def is_professional(self):
        return self.role == self.Role.PROFESSIONAL

    def is_hr(self):
        return self.role == self.Role.HR

    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def role_badge_color(self):
        colors = {
            self.Role.PARTICIPANT: 'primary',
            self.Role.COORDINATOR: 'success',
            self.Role.PROFESSIONAL: 'info',
            self.Role.HR: 'warning',
            self.Role.ADMIN: 'danger',
        }
        return colors.get(self.role, 'secondary')

    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} ({self.username}) [{self.get_role_display()}]"
        return f"{self.username} [{self.get_role_display()}]"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-heart-pulse', help_text="Bootstrap icon class")
    color = models.CharField(max_length=20, default='#0d9488', help_text="Hex color or theme identifier")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Program(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'UPCOMING', 'Upcoming'
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='programs')
    coordinator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='coordinated_programs',
        limit_choices_to={'role': User.Role.COORDINATOR}
    )
    assigned_professional = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_programs',
        limit_choices_to={'role': User.Role.PROFESSIONAL}
    )
    start_date = models.DateField()
    end_date = models.DateField()
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum number of enrolled participants"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', 'title']

    def clean(self):
        super().clean()
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({'end_date': 'End date must be on or after start date.'})
        if self.capacity is not None and self.capacity < 1:
            raise ValidationError({'capacity': 'Capacity must be at least 1.'})

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status='ENROLLED').count()

    @property
    def is_full(self):
        return self.enrolled_count >= self.capacity

    @property
    def available_spots(self):
        return max(0, self.capacity - self.enrolled_count)

    @property
    def average_rating(self):
        feedbacks = self.feedbacks.all()
        if not feedbacks.exists():
            return None
        total = sum(f.rating for f in feedbacks)
        return round(total / feedbacks.count(), 1)

    @property
    def conducted_sessions_count(self):
        return self.sessions.filter(is_completed=True).count()

    @property
    def total_sessions_count(self):
        return self.sessions.count()

    @property
    def program_participation_rate(self):
        """Aggregate participation rate across all enrolled participants and conducted sessions"""
        conducted = self.conducted_sessions_count
        if conducted == 0:
            return 0.0
        enrolled = self.enrollments.filter(status='ENROLLED')
        if not enrolled.exists():
            return 0.0
        total_possible = enrolled.count() * conducted
        total_attended = Attendance.objects.filter(
            session__program=self,
            session__is_completed=True,
            enrollment__status='ENROLLED',
            attended=True
        ).count()
        return round((total_attended / total_possible) * 100, 1) if total_possible > 0 else 0.0

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Session(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, default='Wellness Studio / Online Zoom')
    is_completed = models.BooleanField(default=False, help_text="Mark when session has been conducted")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session_date', 'start_time']

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})

    @property
    def attended_count(self):
        return self.attendances.filter(attended=True).count()

    def __str__(self):
        return f"{self.program.title} - {self.title} ({self.session_date})"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = 'ENROLLED', 'Enrolled'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENROLLED)

    class Meta:
        unique_together = ('user', 'program')
        ordering = ['-enrolled_at']

    def clean(self):
        super().clean()
        # Verify capacity when enrolling a new participant
        if not self.pk and self.status == self.Status.ENROLLED:
            if self.program.is_full:
                raise ValidationError(f"Program '{self.program.title}' is already at full capacity ({self.program.capacity}).")

    @property
    def attended_sessions_count(self):
        return Attendance.objects.filter(
            enrollment=self,
            session__is_completed=True,
            attended=True
        ).count()

    @property
    def conducted_sessions_count(self):
        return self.program.sessions.filter(is_completed=True).count()

    @property
    def participation_rate(self):
        conducted = self.conducted_sessions_count
        if conducted == 0:
            return 0.0
        attended = self.attended_sessions_count
        return round((attended / conducted) * 100, 1)

    @property
    def is_eligible_for_reward(self):
        # Business rule: sessions attended / sessions conducted x 100 >= 75%
        return self.conducted_sessions_count >= 1 and self.participation_rate >= 75.0

    def __str__(self):
        return f"{self.user.username} in {self.program.title} ({self.get_status_display()})"


class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendances')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendances')
    attended = models.BooleanField(default=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(auto_now=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('session', 'enrollment')

    def __str__(self):
        status = "Present" if self.attended else "Absent"
        return f"{self.enrollment.user.username} - {self.session.title}: {status}"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    log_date = models.DateField(default=timezone.now)
    steps = models.PositiveIntegerField(default=0, help_text="Total daily steps")
    workout_minutes = models.PositiveIntegerField(default=0, help_text="Workout / exercise time in minutes")
    water_intake_ml = models.PositiveIntegerField(default=0, help_text="Water consumed in milliliters (e.g. 2500)")
    sleep_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=7.0,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        help_text="Hours of sleep"
    )
    meals_notes = models.TextField(blank=True, help_text="Meals, nutrition details, energy level, or notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-log_date', '-created_at']

    def __str__(self):
        return f"{self.user.username} Activity on {self.log_date}"


class Goal(models.Model):
    class GoalType(models.TextChoices):
        STEPS = 'STEPS', 'Daily Steps'
        WORKOUT = 'WORKOUT', 'Workout Minutes'
        WATER = 'WATER', 'Water Intake (ml)'
        SLEEP = 'SLEEP', 'Sleep Hours'
        OTHER = 'OTHER', 'Custom Goal'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    goal_type = models.CharField(max_length=20, choices=GoalType.choices, default=GoalType.STEPS)
    target_value = models.DecimalField(max_digits=8, decimal_places=1, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=50, default='steps')
    target_date = models.DateField(null=True, blank=True)
    is_achieved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_achieved', '-created_at']

    def __str__(self):
        return f"{self.user.username}'s Goal: {self.title} ({self.target_value} {self.unit})"


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'Program Announcement'
        SESSION_REMINDER = 'SESSION_REMINDER', 'Session Reminder'
        GOAL_ACHIEVED = 'GOAL_ACHIEVED', 'Goal Achievement'
        REWARD = 'REWARD', 'Reward Eligibility'
        GENERAL = 'GENERAL', 'General'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.user.username}: {self.title}"


class Feedback(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='feedbacks')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 (poor) to 5 (excellent)"
    )
    comments = models.TextField(help_text="Participant comments and feedback")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('program', 'participant')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.participant.username} -> {self.program.title}: {self.rating} stars"


class ProgressNote(models.Model):
    class NoteType(models.TextChoices):
        RECOMMENDATION = 'RECOMMENDATION', 'Professional Recommendation'
        OBSERVATION = 'OBSERVATION', 'Clinical / Wellness Observation'
        MILESTONE = 'MILESTONE', 'Milestone Recognition'

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='progress_notes')
    professional = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='professional_notes',
        limit_choices_to={'role': User.Role.PROFESSIONAL}
    )
    participant = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='progress_notes',
        help_text="Optional: Leave blank for a program-wide note/recommendation"
    )
    note_type = models.CharField(max_length=30, choices=NoteType.choices, default=NoteType.RECOMMENDATION)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.participant.username if self.participant else "All Participants"
        return f"[{self.get_note_type_display()}] {self.program.title} -> {target}: {self.title}"
