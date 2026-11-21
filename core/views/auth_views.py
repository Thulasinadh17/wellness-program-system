from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from core.models import User, Program, Category
from core.forms import ParticipantRegistrationForm


def home_view(request):
    """Public home/landing page with programs preview and portal introduction."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    
    categories = Category.objects.all()[:4]
    featured_programs = Program.objects.filter(status__in=['UPCOMING', 'ACTIVE']).select_related('category', 'coordinator')[:6]
    stats = {
        'programs_count': Program.objects.count(),
        'participants_count': User.objects.filter(role=User.Role.PARTICIPANT).count(),
        'categories_count': Category.objects.count(),
    }
    return render(request, 'index.html', {
        'categories': categories,
        'featured_programs': featured_programs,
        'stats': stats,
    })


def login_view(request):
    """User login view supporting standard authentication and quick demo logins."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """Log out current user."""
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('login')


def register_view(request):
    """Self-registration exclusively for Participants."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = ParticipantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to the Wellness System, {user.first_name}! You are registered as a Participant.")
            return redirect('participant_dashboard')
        else:
            messages.error(request, "Please correct the registration errors below.")
    else:
        form = ParticipantRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


@login_required
def dashboard_redirect(request):
    """Router redirecting each user role to their dedicated dashboard."""
    role = request.user.role
    if role == User.Role.COORDINATOR:
        return redirect('coordinator_dashboard')
    elif role == User.Role.PROFESSIONAL:
        return redirect('professional_dashboard')
    elif role == User.Role.HR:
        return redirect('hr_dashboard')
    elif role == User.Role.ADMIN or request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return redirect('participant_dashboard')


@login_required
def password_change_view(request):
    """Allow users to change their password securely."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'auth/password_change.html', {'form': form})


def custom_permission_denied_view(request, exception=None):
    """Custom 403 Forbidden page for unauthorized role access."""
    return render(request, '403.html', {'exception': exception}, status=403)


def custom_not_found_view(request, exception=None):
    """Custom 404 page."""
    return render(request, '404.html', status=404)


def custom_server_error_view(request):
    """Custom 500 page."""
    return render(request, '500.html', status=500)
