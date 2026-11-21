import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Q
from core.models import (
    Program, Session, Enrollment, Attendance, Notification, User, Category
)
from core.forms import ProgramForm, SessionForm, AnnouncementForm
from core.decorators import coordinator_required


@coordinator_required
def coordinator_dashboard(request):
    """Coordinator main dashboard displaying managed programs, participant stats, and upcoming schedule."""
    coordinator = request.user
    programs = Program.objects.filter(coordinator=coordinator).select_related('category', 'assigned_professional')
    
    total_programs = programs.count()
    active_programs = programs.filter(status='ACTIVE').count()
    total_enrollments = Enrollment.objects.filter(program__coordinator=coordinator, status='ENROLLED').count()
    
    # Upcoming sessions for coordinator's programs
    upcoming_sessions = Session.objects.filter(
        program__coordinator=coordinator,
        session_date__gte=timezone.now().date(),
        is_completed=False
    ).select_related('program').order_by('session_date', 'start_time')[:6]

    return render(request, 'coordinator/dashboard.html', {
        'programs': programs,
        'total_programs': total_programs,
        'active_programs': active_programs,
        'total_enrollments': total_enrollments,
        'upcoming_sessions': upcoming_sessions,
    })


@coordinator_required
def program_create_view(request):
    """Create a new wellness program."""
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save(commit=False)
            program.coordinator = request.user
            program.save()
            messages.success(request, f"Program '{program.title}' created successfully!")
            return redirect('coordinator_program_detail', program_id=program.id)
        else:
            messages.error(request, "Please correct the errors in the program form.")
    else:
        form = ProgramForm(initial={
            'start_date': timezone.now().date(),
            'end_date': (timezone.now() + timezone.timedelta(days=30)).date(),
            'capacity': 25,
            'status': 'UPCOMING',
        })

    return render(request, 'coordinator/program_form.html', {
        'form': form,
        'title': 'Create New Wellness Program',
    })


@coordinator_required
def program_edit_view(request, program_id):
    """Edit an existing program owned by the coordinator."""
    program = get_object_or_404(Program, id=program_id, coordinator=request.user)

    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, f"Program '{program.title}' updated successfully.")
            return redirect('coordinator_program_detail', program_id=program.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProgramForm(instance=program)

    return render(request, 'coordinator/program_form.html', {
        'form': form,
        'program': program,
        'title': f'Edit Program: {program.title}',
    })


@coordinator_required
def program_cancel_view(request, program_id):
    """Cancel a program and notify all enrolled participants."""
    program = get_object_or_404(Program, id=program_id, coordinator=request.user)
    if request.method == 'POST':
        program.status = 'CANCELLED'
        program.save()

        # Notify participants
        enrolled_users = User.objects.filter(enrollments__program=program, enrollments__status='ENROLLED')
        for user in enrolled_users:
            Notification.objects.create(
                user=user,
                title=f"Program Cancelled: {program.title}",
                message=f"Please note that '{program.title}' has been cancelled by the wellness coordinator.",
                notification_type=Notification.NotificationType.ANNOUNCEMENT
            )

        messages.warning(request, f"Program '{program.title}' has been marked as Cancelled.")
    return redirect('coordinator_program_detail', program_id=program.id)


@coordinator_required
def coordinator_program_detail(request, program_id):
    """Detailed management view of a program: enrollments, sessions, and announcement tools."""
    program = get_object_or_404(
        Program.objects.select_related('category', 'assigned_professional'),
        id=program_id,
        coordinator=request.user
    )

    enrollments = program.enrollments.select_related('user').order_by('status', '-enrolled_at')
    sessions = program.sessions.all().order_by('session_date', 'start_time')
    announcement_form = AnnouncementForm()

    return render(request, 'coordinator/program_detail.html', {
        'program': program,
        'enrollments': enrollments,
        'sessions': sessions,
        'announcement_form': announcement_form,
    })


@coordinator_required
def remove_enrollment_view(request, program_id, enrollment_id):
    """Coordinator removes or rejects an enrollment."""
    program = get_object_or_404(Program, id=program_id, coordinator=request.user)
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, program=program)

    if request.method == 'POST':
        enrollment.status = 'REJECTED'
        enrollment.save()
        messages.info(request, f"Removed participant {enrollment.user.get_full_name() or enrollment.user.username} from program.")
    return redirect('coordinator_program_detail', program_id=program.id)


@coordinator_required
def session_create_view(request, program_id):
    """Schedule a new session within a program."""
    program = get_object_or_404(Program, id=program_id, coordinator=request.user)

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.program = program
            session.save()
            messages.success(request, f"Session '{session.title}' scheduled.")
            return redirect('coordinator_program_detail', program_id=program.id)
        else:
            messages.error(request, "Please check the session details.")
    else:
        form = SessionForm(initial={'session_date': program.start_date})

    return render(request, 'coordinator/session_form.html', {
        'form': form,
        'program': program,
        'title': f'Schedule Session for {program.title}',
    })


@coordinator_required
def session_edit_view(request, program_id, session_id):
    """Edit an existing session."""
    program = get_object_or_404(Program, id=program_id, coordinator=request.user)
    session = get_object_or_404(Session, id=session_id, program=program)

    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, f"Session '{session.title}' updated.")
            return redirect('coordinator_program_detail', program_id=program.id)
        else:
            messages.error(request, "Please check session errors.")
    else:
        form = SessionForm(instance=session)

    return render(request, 'coordinator/session_form.html', {
        'form': form,
        'program': program,
        'session': session,
        'title': f'Edit Session: {session.title}',
    })


@coordinator_required
def mark_attendance_view(request, program_id, session_id):
    """Mark attendance for all enrolled participants for a given session."""
    program = get_object_or_404(Program, id=program_id, coordinator=request.user)
    session = get_object_or_404(Session, id=session_id, program=program)
    enrollments = Enrollment.objects.filter(program=program, status='ENROLLED').select_related('user')

    # Existing attendance records
    existing_attendances = {
        att.enrollment_id: att for att in Attendance.objects.filter(session=session)
    }

    if request.method == 'POST':
        attended_ids = request.POST.getlist('attended_enrollments')
        attended_set = set(map(int, attended_ids))

        for enr in enrollments:
            is_present = enr.id in attended_set
            notes = request.POST.get(f'notes_{enr.id}', '')
            
            Attendance.objects.update_or_create(
                session=session,
                enrollment=enr,
                defaults={
                    'attended': is_present,
                    'notes': notes,
                    'marked_by': request.user,
                }
            )

            # Check if participant is now eligible for reward (participation >= 75%)
            if is_present and enr.is_eligible_for_reward:
                # Add reward points if not already awarded
                Notification.objects.get_or_create(
                    user=enr.user,
                    title="Eligible for Wellness Reward! 🎖️",
                    notification_type=Notification.NotificationType.REWARD,
                    defaults={
                        'message': f"Great job! Your attendance in '{program.title}' reached {enr.participation_rate}% (>= 75%). You are eligible for the wellness completion reward!",
                    }
                )

        session.is_completed = True
        session.save()
        messages.success(request, f"Attendance recorded for '{session.title}'! Session marked as completed.")
        return redirect('coordinator_program_detail', program_id=program.id)

    # Prepare rows for template
    rows = []
    for enr in enrollments:
        att = existing_attendances.get(enr.id)
        rows.append({
            'enrollment': enr,
            'attended': att.attended if att else False,
            'notes': att.notes if att else '',
        })

    return render(request, 'coordinator/attendance.html', {
        'program': program,
        'session': session,
        'rows': rows,
    })


@coordinator_required
def send_announcement_view(request, program_id):
    """Broadcast an announcement to all enrolled participants in a program."""
    program = get_object_or_404(Program, id=program_id, coordinator=request.user)

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            message = form.cleaned_data['message']

            enrolled_users = User.objects.filter(enrollments__program=program, enrollments__status='ENROLLED')
            count = 0
            for user in enrolled_users:
                Notification.objects.create(
                    user=user,
                    title=f"[{program.title}] {title}",
                    message=message,
                    notification_type=Notification.NotificationType.ANNOUNCEMENT
                )
                count += 1

            messages.success(request, f"Announcement sent to {count} enrolled participant(s)!")
        else:
            messages.error(request, "Failed to send announcement. Please check form fields.")

    return redirect('coordinator_program_detail', program_id=program.id)


@coordinator_required
def coordinator_reports_view(request):
    """Participation reports view with aggregation and CSV download."""
    coordinator = request.user
    programs = Program.objects.filter(coordinator=coordinator).select_related('category')

    reports = []
    for prog in programs:
        enrollments = prog.enrollments.filter(status='ENROLLED').select_related('user')
        conducted = prog.conducted_sessions_count
        reward_eligible = sum(1 for e in enrollments if e.is_eligible_for_reward)
        reports.append({
            'program': prog,
            'enrolled_count': enrollments.count(),
            'conducted_sessions': conducted,
            'overall_rate': prog.program_participation_rate,
            'reward_eligible_count': reward_eligible,
            'enrollments': enrollments,
        })

    return render(request, 'coordinator/reports.html', {'reports': reports})


@coordinator_required
def export_participation_csv(request):
    """Generate downloadable CSV of program participation statistics."""
    coordinator = request.user
    programs = Program.objects.filter(coordinator=coordinator)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="wellness_participation_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Program Title', 'Category', 'Participant Username', 'Participant Name',
        'Department', 'Status', 'Sessions Conducted', 'Sessions Attended',
        'Participation %', 'Eligible for Reward'
    ])

    for prog in programs:
        enrollments = prog.enrollments.select_related('user').all()
        conducted = prog.conducted_sessions_count
        for enr in enrollments:
            attended = enr.attended_sessions_count
            rate = enr.participation_rate
            eligible = 'YES' if enr.is_eligible_for_reward else 'NO'
            writer.writerow([
                prog.title,
                prog.category.name,
                enr.user.username,
                enr.user.get_full_name() or enr.user.username,
                enr.user.department,
                enr.get_status_display(),
                conducted,
                attended,
                f"{rate}%",
                eligible
            ])

    return response
