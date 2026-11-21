from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    User, Program, Session, ActivityLog, Goal, Feedback, ProgressNote, Category
)


class ParticipantRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    department = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department / Unit (e.g., Engineering)'}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'department', 'phone_number')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PARTICIPANT
        if commit:
            user.save()
        return user


class UserAdminForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep current password'}),
        help_text="Required when creating a new user"
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'role',
            'department', 'professional_title', 'is_active', 'points'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'professional_title': forms.TextInput(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.instance.pk and not password:
            raise ValidationError("Password is required for newly created user.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = [
            'title', 'description', 'category', 'assigned_professional',
            'start_date', 'end_date', 'capacity', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 8-Week Core Fitness Challenge'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Program overview, objectives, and syllabus'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'assigned_professional': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'e.g., 25'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit assigned_professional to professionals
        self.fields['assigned_professional'].queryset = User.objects.filter(role=User.Role.PROFESSIONAL, is_active=True)
        self.fields['assigned_professional'].empty_label = "-- Select Wellness Professional (Optional) --"

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        capacity = cleaned_data.get('capacity')

        if start and end and end < start:
            self.add_error('end_date', "End date must be on or after start date.")
        if capacity is not None and capacity < 1:
            self.add_error('capacity', "Capacity must be at least 1.")
        return cleaned_data


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['title', 'description', 'session_date', 'start_time', 'end_time', 'location', 'is_completed']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Session 1: Nutrition Fundamentals'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Topics covered, requirements'}),
            'session_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Room 204 / Zoom link'}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and end <= start:
            self.add_error('end_time', "Session end time must be after start time.")
        return cleaned_data


class AnnouncementForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Announcement Subject'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your announcement to all enrolled participants...'})
    )


class ActivityLogForm(forms.ModelForm):
    class Meta:
        model = ActivityLog
        fields = ['log_date', 'steps', 'workout_minutes', 'water_intake_ml', 'sleep_hours', 'meals_notes']
        widgets = {
            'log_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'steps': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'e.g., 8500'}),
            'workout_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'e.g., 45'}),
            'water_intake_ml': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'e.g., 2500'}),
            'sleep_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 24, 'step': '0.5', 'placeholder': 'e.g., 7.5'}),
            'meals_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Meals logged, hydration reminders, wellness notes...'}),
        }

    def clean_steps(self):
        val = self.cleaned_data.get('steps', 0)
        if val < 0:
            raise ValidationError("Steps cannot be negative.")
        return val

    def clean_workout_minutes(self):
        val = self.cleaned_data.get('workout_minutes', 0)
        if val < 0:
            raise ValidationError("Workout minutes cannot be negative.")
        return val

    def clean_water_intake_ml(self):
        val = self.cleaned_data.get('water_intake_ml', 0)
        if val < 0:
            raise ValidationError("Water intake cannot be negative.")
        return val


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'goal_type', 'target_value', 'unit', 'target_date', 'is_achieved']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Walk 10k steps daily'}),
            'goal_type': forms.Select(attrs={'class': 'form-select'}),
            'target_value': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 'any', 'placeholder': 'Target numeric value'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'steps, mins, ml, hours'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_achieved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_target_value(self):
        val = self.cleaned_data.get('target_value', 0)
        if val is not None and val < 0:
            raise ValidationError("Target value cannot be negative.")
        return val


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comments']
        widgets = {
            'rating': forms.Select(
                choices=[(5, '⭐⭐⭐⭐⭐ (5 - Excellent)'), (4, '⭐⭐⭐⭐ (4 - Very Good)'), (3, '⭐⭐⭐ (3 - Good)'), (2, '⭐⭐ (2 - Fair)'), (1, '⭐ (1 - Poor)')],
                attrs={'class': 'form-select'}
            ),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share what you loved and suggestions for improvement...'}),
        }


class ProgressNoteForm(forms.ModelForm):
    class Meta:
        model = ProgressNote
        fields = ['participant', 'note_type', 'title', 'content']
        widgets = {
            'participant': forms.Select(attrs={'class': 'form-select'}),
            'note_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Note title / summary'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Clinical observations, personalized advice, or milestones...'}),
        }

    def __init__(self, program, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only enrolled participants of this program can be chosen
        enrolled_users = User.objects.filter(enrollments__program=program, enrollments__status='ENROLLED')
        self.fields['participant'].queryset = enrolled_users
        self.fields['participant'].empty_label = "-- Entire Program (All Participants) --"
        self.fields['participant'].required = False


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mental Health & Mindfulness'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Category description'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-heart-pulse, bi-apple, bi-flower1, bi-shield-check'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }
