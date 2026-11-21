import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from core.models import (
    Program, Enrollment, Session, ActivityLog, Goal, Notification, Feedback, Category, User, ProgressNote
)
from core.forms import ActivityLogForm, GoalForm, FeedbackForm
from core.decorators import participant_required


@participant_required
def participant_dashboard(request):
    """Participant personal wellness dashboard with stats, progress charts, and upcoming sessions."""
    user = request.user
    
    # Enrollments
    enrollments = Enrollment.objects.filter(user=user, status='ENROLLED').select_related('program', 'program__category')
    enrolled_program_ids = enrollments.values_list('program_id', flat=True)
    
    # Upcoming sessions for enrolled programs
    upcoming_sessions = Session.objects.filter(
        program_id__in=enrolled_program_ids,
        session_date__gte=timezone.now().date(),
        is_completed=False
    ).select_related('program').order_by('session_date', 'start_time')[:5]

    # Calculate overall participation rate
    total_conducted = 0
    total_attended = 0
    reward_eligible_count = 0
    
    program_participation_data = []
    for enr in enrollments:
        conducted = enr.conducted_sessions_count
        attended = enr.attended_sessions_count
        rate = enr.participation_rate
        total_conducted += conducted
        total_attended += attended
        if enr.is_eligible_for_reward:
            reward_eligible_count += 1
        program_participation_data.append({
            'title': enr.program.title,
            'rate': rate,
            'attended': attended,
            'conducted': conducted,
            'eligible': enr.is_eligible_for_reward,
        })

    overall_participation = round((total_attended / total_conducted) * 100, 1) if total_conducted > 0 else 0.0

    # Activity stats for the last 7 days
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)
    recent_logs = ActivityLog.objects.filter(user=user, log_date__gte=seven_days_ago).order_by('log_date')

    # Prepare chart dates and data
    date_labels = []
    steps_data = []
    workout_data = []
    sleep_data = []
    water_data = []

    logs_by_date = {log.log_date: log for log in recent_logs}
    for i in range(7):
        current_date = seven_days_ago + timedelta(days=i)
        date_str = current_date.strftime('%b %d')
        date_labels.append(date_str)
        log = logs_by_date.get(current_date)
        if log:
            steps_data.append(log.steps)
            workout_data.append(log.workout_minutes)
            sleep_data.append(float(log.sleep_hours))
            water_data.append(log.water_intake_ml)
        else:
            steps_data.append(0)
            workout_data.append(0)
            sleep_data.append(0)
            water_data.append(0)

    # Active goals
    active_goals = Goal.objects.filter(user=user, is_achieved=False)[:4]
    
    # Recent notifications
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:4]

    context = {
        'enrollments': enrollments,
        'upcoming_sessions': upcoming_sessions,
        'overall_participation': overall_participation,
        'reward_eligible_count': reward_eligible_count,
        'program_participation_data': program_participation_data,
        'active_goals': active_goals,
        'notifications': notifications,
        # Chart JSON data
        'chart_labels': json.dumps(date_labels),
        'steps_data': json.dumps(steps_data),
        'workout_data': json.dumps(workout_data),
        'sleep_data': json.dumps(sleep_data),
        'water_data': json.dumps(water_data),
        'program_chart_labels': json.dumps([item['title'][:20] for item in program_participation_data]),
        'program_chart_rates': json.dumps([item['rate'] for item in program_participation_data]),
    }
    return render(request, 'participant/dashboard.html', context)


@participant_required
def program_browse_view(request):
    """Browse, search, and filter programs with category and status tags."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    status_filter = request.GET.get('status')

    programs = Program.objects.all().select_related('category', 'coordinator', 'assigned_professional')

    if query:
        programs = programs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    if category_id:
        programs = programs.filter(category_id=category_id)
    if status_filter:
        programs = programs.filter(status=status_filter)

    categories = Category.objects.all()

    # User enrollment mapping
    user_enrolled_program_ids = set(
        Enrollment.objects.filter(user=request.user, status='ENROLLED').values_list('program_id', flat=True)
    )

    paginator = Paginator(programs, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'participant/program_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'selected_status': status_filter,
        'query': query,
        'user_enrolled_program_ids': user_enrolled_program_ids,
    })


@participant_required
def program_detail_view(request, program_id):
    """View details of a specific program, sessions schedule, professional recommendations, and reviews."""
    program = get_object_or_404(Program.objects.select_related('category', 'coordinator', 'assigned_professional'), id=program_id)
    user_enrollment = Enrollment.objects.filter(user=request.user, program=program).first()
    is_enrolled = user_enrollment is not None and user_enrollment.status == 'ENROLLED'

    sessions = program.sessions.all().order_by('session_date', 'start_time')
    feedbacks = program.feedbacks.all().select_related('participant').order_by('-submitted_at')
    user_feedback = feedbacks.filter(participant=request.user).first()
    
    # Professional recommendations visible to this participant (or program-wide)
    progress_notes = ProgressNote.objects.filter(
        program=program
    ).filter(
        Q(participant__isnull=True) | Q(participant=request.user)
    ).order_by('-created_at')

    feedback_form = FeedbackForm()

    return render(request, 'participant/program_detail.html', {
        'program': program,
        'user_enrollment': user_enrollment,
        'is_enrolled': is_enrolled,
        'sessions': sessions,
        'feedbacks': feedbacks,
        'user_feedback': user_feedback,
        'feedback_form': feedback_form,
        'progress_notes': progress_notes,
    })


@participant_required
def program_enroll_view(request, program_id):
    """Enroll in a program with strict capacity and duplicate verification."""
    if request.method != 'POST':
        return redirect('program_detail', program_id=program_id)

    program = get_object_or_404(Program, id=program_id)
    user = request.user

    # Rule 1: Cannot enroll in cancelled or completed programs
    if program.status in ['COMPLETED', 'CANCELLED']:
        messages.error(request, f"Enrollment is closed because this program is {program.get_status_display().lower()}.")
        return redirect('program_detail', program_id=program_id)

    # Rule 2: Cannot enroll twice
    existing_enrollment = Enrollment.objects.filter(user=user, program=program).first()
    if existing_enrollment and existing_enrollment.status == 'ENROLLED':
        messages.warning(request, f"You are already enrolled in '{program.title}'.")
        return redirect('program_detail', program_id=program_id)

    # Rule 3: Capacity can never be exceeded
    if program.is_full:
        messages.error(request, f"Cannot enroll: '{program.title}' is already full (Capacity: {program.capacity}).")
        return redirect('program_detail', program_id=program_id)

    if existing_enrollment:
        existing_enrollment.status = 'ENROLLED'
        existing_enrollment.save()
    else:
        Enrollment.objects.create(user=user, program=program, status='ENROLLED')

    # Send confirmation notification
    Notification.objects.create(
        user=user,
        title=f"Enrolled in {program.title}",
        message=f"You have successfully enrolled in {program.title}. Check the session schedule to attend upcoming workshops!",
        notification_type=Notification.NotificationType.GENERAL
    )

    messages.success(request, f"🎉 You have successfully enrolled in '{program.title}'!")
    return redirect('program_detail', program_id=program_id)


@participant_required
def program_withdraw_view(request, program_id):
    """Withdraw from an enrolled program."""
    if request.method != 'POST':
        return redirect('program_detail', program_id=program_id)

    program = get_object_or_404(Program, id=program_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, program=program)

    if enrollment.status == 'ENROLLED':
        enrollment.status = 'WITHDRAWN'
        enrollment.save()
        messages.info(request, f"You have withdrawn from '{program.title}'.")
    return redirect('program_detail', program_id=program_id)


@participant_required
def submit_feedback_view(request, program_id):
    """Submit program rating and feedback."""
    program = get_object_or_404(Program, id=program_id)
    enrollment = Enrollment.objects.filter(user=request.user, program=program, status='ENROLLED').first()

    if not enrollment:
        messages.error(request, "Only enrolled participants can submit feedback.")
        return redirect('program_detail', program_id=program_id)

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback, created = Feedback.objects.update_or_create(
                program=program,
                participant=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comments': form.cleaned_data['comments'],
                }
            )
            messages.success(request, "Thank you! Your feedback has been submitted.")
        else:
            messages.error(request, "Invalid feedback. Please check your submission.")
    return redirect('program_detail', program_id=program_id)


@participant_required
def activity_log_view(request):
    """View activity history and log daily wellness stats."""
    user = request.user

    if request.method == 'POST':
        form = ActivityLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = user
            log.save()

            # Award points for logging wellness activity
            user.points += 10
            user.save()

            messages.success(request, "Activity logged successfully! You earned +10 wellness points! 🌟")
            return redirect('activity_log')
        else:
            messages.error(request, "Error logging activity. Please check input values.")
    else:
        form = ActivityLogForm(initial={'log_date': timezone.now().date()})

    logs = ActivityLog.objects.filter(user=user).order_by('-log_date', '-created_at')
    paginator = Paginator(logs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'participant/activity_log.html', {
        'form': form,
        'page_obj': page_obj,
    })


@participant_required
def delete_activity_log(request, log_id):
    """Delete an activity log entry."""
    log = get_object_or_404(ActivityLog, id=log_id, user=request.user)
    if request.method == 'POST':
        log.delete()
        messages.info(request, "Activity log entry removed.")
    return redirect('activity_log')


@participant_required
def goals_view(request):
    """View, create, and manage wellness goals."""
    user = request.user

    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = user
            goal.save()
            messages.success(request, f"New goal '{goal.title}' created! Let's crush it! 💪")
            return redirect('goals_list')
        else:
            messages.error(request, "Please check the goal fields.")
    else:
        form = GoalForm()

    goals = Goal.objects.filter(user=user).order_by('is_achieved', '-created_at')
    return render(request, 'participant/goals.html', {
        'form': form,
        'goals': goals,
    })


@participant_required
def toggle_goal_view(request, goal_id):
    """Toggle a goal achievement status."""
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    if request.method == 'POST':
        goal.is_achieved = not goal.is_achieved
        goal.save()
        if goal.is_achieved:
            request.user.points += 50
            request.user.save()
            Notification.objects.create(
                user=request.user,
                title="Goal Achieved! 🏆",
                message=f"Congratulations! You completed your goal: '{goal.title}'. You earned +50 points!",
                notification_type=Notification.NotificationType.GOAL_ACHIEVED
            )
            messages.success(request, f"Awesome! '{goal.title}' marked as achieved! (+50 points)")
        else:
            messages.info(request, f"'{goal.title}' marked back as in-progress.")
    return redirect('goals_list')


@participant_required
def notifications_view(request):
    """View and manage in-app notifications inbox."""
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('notifications_inbox')

    paginator = Paginator(notifications, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'participant/notifications.html', {'page_obj': page_obj})
