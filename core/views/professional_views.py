from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from core.models import Program, ProgressNote, User, Enrollment, Notification
from core.forms import ProgressNoteForm
from core.decorators import professional_required


@professional_required
def professional_dashboard(request):
    """Wellness Professional dashboard showing assigned programs, participants, and notes."""
    pro = request.user
    assigned_programs = Program.objects.filter(assigned_professional=pro).select_related('category', 'coordinator')
    
    total_assigned_programs = assigned_programs.count()
    total_participants = Enrollment.objects.filter(
        program__assigned_professional=pro,
        status='ENROLLED'
    ).count()

    recent_notes = ProgressNote.objects.filter(professional=pro).select_related('program', 'participant').order_by('-created_at')[:8]

    return render(request, 'professional/dashboard.html', {
        'assigned_programs': assigned_programs,
        'total_assigned_programs': total_assigned_programs,
        'total_participants': total_participants,
        'recent_notes': recent_notes,
    })


@professional_required
def professional_program_detail(request, program_id):
    """View assigned program syllabus, participants, and manage clinical/wellness notes."""
    program = get_object_or_404(
        Program.objects.select_related('category', 'coordinator'),
        id=program_id,
        assigned_professional=request.user
    )

    enrollments = program.enrollments.filter(status='ENROLLED').select_related('user')
    sessions = program.sessions.all().order_by('session_date')
    notes = program.progress_notes.filter(professional=request.user).select_related('participant').order_by('-created_at')

    if request.method == 'POST':
        form = ProgressNoteForm(program, request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.program = program
            note.professional = request.user
            note.save()

            # If note was addressed to a specific participant, notify them!
            if note.participant:
                Notification.objects.create(
                    user=note.participant,
                    title=f"New Note from {request.user.get_full_name() or request.user.username}",
                    message=f"A new {note.get_note_type_display().lower()} has been added for '{program.title}': {note.title}",
                    notification_type=Notification.NotificationType.GENERAL
                )

            messages.success(request, f"Progress note '{note.title}' recorded.")
            return redirect('professional_program_detail', program_id=program.id)
        else:
            messages.error(request, "Failed to save note. Please verify form fields.")
    else:
        form = ProgressNoteForm(program)

    return render(request, 'professional/program_detail.html', {
        'program': program,
        'enrollments': enrollments,
        'sessions': sessions,
        'notes': notes,
        'form': form,
    })
