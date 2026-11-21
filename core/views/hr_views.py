import json
from datetime import timedelta
from django.shortcuts import render
from django.db.models import Avg, Count, Q
from django.utils import timezone
from core.models import Program, Enrollment, Feedback, ActivityLog, User, Category
from core.decorators import hr_required


@hr_required
def hr_dashboard(request):
    """
    HR and Executive Management aggregate wellness intelligence dashboard.
    Strictly aggregates data without exposing individual personal health details.
    """
    # High-level KPIs
    total_participants = User.objects.filter(role=User.Role.PARTICIPANT).count()
    total_programs = Program.objects.count()
    active_programs = Program.objects.filter(status='ACTIVE').count()
    total_enrollments = Enrollment.objects.filter(status='ENROLLED').count()

    overall_feedback = Feedback.objects.aggregate(avg_rating=Avg('rating'))['avg_rating']
    avg_satisfaction = round(overall_feedback, 1) if overall_feedback else 0.0

    # Chart 1: Programs summary
    programs = Program.objects.all().select_related('category')

    prog_titles = []
    prog_enrollments = []
    prog_rates = []
    prog_ratings = []

    for p in programs:
        prog_titles.append(p.title[:20])
        prog_enrollments.append(p.enrolled_count)
        prog_rates.append(p.program_participation_rate)
        rating = p.average_rating
        prog_ratings.append(rating if rating is not None else 0.0)

    # Chart 2: Category Distribution
    categories = Category.objects.annotate(program_count=Count('programs'))
    cat_labels = [c.name for c in categories]
    cat_counts = [c.program_count for c in categories]

    # Chart 3: Aggregate Organization Activity Trends (Last 14 days) - Strictly Anonymized
    today = timezone.now().date()
    fourteen_days_ago = today - timedelta(days=13)

    trend_dates = []
    avg_steps_trend = []
    avg_workout_trend = []

    for i in range(14):
        day = fourteen_days_ago + timedelta(days=i)
        trend_dates.append(day.strftime('%b %d'))
        daily_stats = ActivityLog.objects.filter(log_date=day).aggregate(
            avg_steps=Avg('steps'),
            avg_workout=Avg('workout_minutes')
        )
        avg_steps_trend.append(round(daily_stats['avg_steps'] or 0))
        avg_workout_trend.append(round(daily_stats['avg_workout'] or 0, 1))

    # Department breakdown (aggregate count of participants per department)
    departments = User.objects.filter(role=User.Role.PARTICIPANT).exclude(department='').values('department').annotate(
        participant_count=Count('id')
    ).order_by('-participant_count')[:6]

    # Program summary table for HR
    program_summaries = []
    for p in programs:
        program_summaries.append({
            'title': p.title,
            'category': p.category.name,
            'status': p.get_status_display(),
            'capacity': p.capacity,
            'enrolled': p.enrolled_count,
            'participation_rate': p.program_participation_rate,
            'avg_rating': p.average_rating or 'N/A',
        })

    context = {
        'total_participants': total_participants,
        'total_programs': total_programs,
        'active_programs': active_programs,
        'total_enrollments': total_enrollments,
        'avg_satisfaction': avg_satisfaction,
        'departments': departments,
        'program_summaries': program_summaries,
        # Chart Data
        'prog_titles_json': json.dumps(prog_titles),
        'prog_enrollments_json': json.dumps(prog_enrollments),
        'prog_rates_json': json.dumps(prog_rates),
        'prog_ratings_json': json.dumps(prog_ratings),
        'cat_labels_json': json.dumps(cat_labels),
        'cat_counts_json': json.dumps(cat_counts),
        'trend_dates_json': json.dumps(trend_dates),
        'avg_steps_trend_json': json.dumps(avg_steps_trend),
        'avg_workout_trend_json': json.dumps(avg_workout_trend),
    }
    return render(request, 'hr/dashboard.html', context)
