from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from core.models import User, Program, Category, Enrollment, ActivityLog, Session
from core.forms import UserAdminForm, CategoryForm
from core.decorators import admin_required


@admin_required
def admin_dashboard(request):
    """Custom Administrative dashboard for managing system entities and system health."""
    total_users = User.objects.count()
    users_by_role = {
        'participants': User.objects.filter(role=User.Role.PARTICIPANT).count(),
        'coordinators': User.objects.filter(role=User.Role.COORDINATOR).count(),
        'professionals': User.objects.filter(role=User.Role.PROFESSIONAL).count(),
        'hr': User.objects.filter(role=User.Role.HR).count(),
        'admins': User.objects.filter(role=User.Role.ADMIN).count(),
    }
    total_programs = Program.objects.count()
    total_sessions = Session.objects.count()
    total_logs = ActivityLog.objects.count()

    recent_enrollments = Enrollment.objects.select_related('user', 'program').order_by('-enrolled_at')[:8]
    recent_users = User.objects.order_by('-date_joined')[:8]

    return render(request, 'admin_dashboard/dashboard.html', {
        'total_users': total_users,
        'users_by_role': users_by_role,
        'total_programs': total_programs,
        'total_sessions': total_sessions,
        'total_logs': total_logs,
        'recent_enrollments': recent_enrollments,
        'recent_users': recent_users,
    })


@admin_required
def user_list_view(request):
    """List, search, and filter system users."""
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role')

    users = User.objects.all().order_by('-date_joined')
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(department__icontains=query)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    paginator = Paginator(users, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_dashboard/user_list.html', {
        'page_obj': page_obj,
        'query': query,
        'role_filter': role_filter,
        'roles': User.Role.choices,
    })


@admin_required
def user_create_view(request):
    """Admin creates a new user of any role."""
    if request.method == 'POST':
        form = UserAdminForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' created with role '{user.get_role_display()}'.")
            return redirect('admin_user_list')
        else:
            messages.error(request, "Failed to create user. Check form validation.")
    else:
        form = UserAdminForm(initial={'role': User.Role.COORDINATOR})

    return render(request, 'admin_dashboard/user_form.html', {
        'form': form,
        'title': 'Create New System User',
    })


@admin_required
def user_edit_view(request, user_id):
    """Admin edits existing user."""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user.username}' updated successfully.")
            return redirect('admin_user_list')
        else:
            messages.error(request, "Please check errors in the form.")
    else:
        form = UserAdminForm(instance=user)

    return render(request, 'admin_dashboard/user_form.html', {
        'form': form,
        'target_user': user,
        'title': f'Edit User: {user.username}',
    })


@admin_required
def user_toggle_status(request, user_id):
    """Toggle user active status."""
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        user.is_active = not user.is_active
        user.save()
        status_text = "activated" if user.is_active else "deactivated"
        messages.info(request, f"User '{user.username}' has been {status_text}.")
    return redirect('admin_user_list')


@admin_required
def category_list_view(request):
    """Manage program categories."""
    categories = Category.objects.annotate(programs_count=Count('programs')).order_by('name')
    return render(request, 'admin_dashboard/category_list.html', {'categories': categories})


@admin_required
def category_create_view(request):
    """Create new program category."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' created.")
            return redirect('admin_category_list')
        else:
            messages.error(request, "Please check errors in category form.")
    else:
        form = CategoryForm(initial={'color': '#0d9488'})

    return render(request, 'admin_dashboard/category_form.html', {
        'form': form,
        'title': 'Create Program Category',
    })


@admin_required
def category_edit_view(request, category_id):
    """Edit existing category."""
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{category.name}' updated.")
            return redirect('admin_category_list')
        else:
            messages.error(request, "Please check errors.")
    else:
        form = CategoryForm(instance=category)

    return render(request, 'admin_dashboard/category_form.html', {
        'form': form,
        'category': category,
        'title': f'Edit Category: {category.name}',
    })


@admin_required
def category_delete_view(request, category_id):
    """Delete a category."""
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.warning(request, f"Category '{name}' deleted.")
    return redirect('admin_category_list')
