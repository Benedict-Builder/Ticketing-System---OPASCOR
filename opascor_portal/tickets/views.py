from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Case, When, IntegerField, Count
from .models import Concern, UserProfile, Message, DEPARTMENT_CHOICES, CATEGORY_CHOICES, SUBCATEGORY_CHOICES
from .forms import ConcernForm, RegisterForm, SUBCATEGORY_MAP
import json

# ─────────────────────────────────────────
# HELPER — redirects admin or regular user
# ─────────────────────────────────────────
def redirect_by_role(user):
    try:
        profile = UserProfile.objects.get(user=user)
        if profile.is_admin:
            return redirect('admin_dashboard')
    except UserProfile.DoesNotExist:
        pass
    return redirect('user_dashboard')

# ─────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect_by_role(user)
        messages.error(request, 'Invalid username or password.')

    return render(request, 'tickets/login.html', {
        'total_users': User.objects.count(),
        'total_tickets': Concern.objects.count(),
        'pending_tickets': Concern.objects.filter(status='Pending').count(),
    })

# ─────────────────────────────────────────
# SEND MESSAGE (user)
# ─────────────────────────────────────────
@login_required
def send_message(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        if subject and body:
            Message.objects.create(
                sender=request.user,
                subject=subject,
                body=body,
            )
            messages.success(request, 'Message sent successfully!')
        else:
            messages.error(request, 'Please fill in all fields.')
    return redirect('user_dashboard')


# ─────────────────────────────────────────
# INBOX (admin)
# ─────────────────────────────────────────
@login_required
def admin_inbox(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin:
        return redirect('user_dashboard')

    msg_id = request.GET.get('read')
    if msg_id:
        Message.objects.filter(id=msg_id).update(is_read=True)

    inbox = Message.objects.order_by('-date_sent').select_related('sender')
    unread_count = inbox.filter(is_read=False).count()

    return render(request, 'tickets/admin_inbox.html', {
        'inbox': inbox,
        'unread_count': unread_count,
        'profile': profile,
    })


# ─────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────
def register_view(request):
    form = RegisterForm(request.POST or None)

    if request.method == 'POST':
        department = request.POST.get('department')
        if not department:
            messages.error(request, 'Please select a department.')
            return render(request, 'tickets/register.html', {
                'form': form,
                'total_users': User.objects.count(),
                'total_tickets': Concern.objects.count(),
                'pending_tickets': Concern.objects.filter(status='Pending').count(),
            })
        if form.is_valid():
            if User.objects.filter(username=form.cleaned_data['username']).exists():
                messages.error(request, 'Username already taken. Please choose another.')
                return render(request, 'tickets/register.html', {
                    'form': form,
                    'total_users': User.objects.count(),
                    'total_tickets': Concern.objects.count(),
                    'pending_tickets': Concern.objects.filter(status='Pending').count(),
                })
            if User.objects.filter(email=form.cleaned_data['email']).exists():
                messages.error(request, 'Email already registered. Please use another.')
                return render(request, 'tickets/register.html', {
                    'form': form,
                    'total_users': User.objects.count(),
                    'total_tickets': Concern.objects.count(),
                    'pending_tickets': Concern.objects.filter(status='Pending').count(),
                })

            full_name = form.cleaned_data['full_name'].split()
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                email=form.cleaned_data['email'],
                first_name=full_name[0],
                last_name=' '.join(full_name[1:]) if len(full_name) > 1 else '',
            )
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'department': department,
                    'is_admin': False
                }
            )
            messages.success(request, 'Account created! Please log in.')
            return redirect('login')

    return render(request, 'tickets/register.html', {
        'form': form,
        'total_users': User.objects.count(),
        'total_tickets': Concern.objects.count(),
        'pending_tickets': Concern.objects.filter(status='Pending').count(),
    })

# ─────────────────────────────────────────
# CHOOSE DEPARTMENT (kept for url compatibility)
# ─────────────────────────────────────────
def choose_department_view(request):
    return redirect('register')

# ─────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────
def logout_view(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────
# USER DASHBOARD
# ─────────────────────────────────────────
@login_required
def user_dashboard(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if profile.is_admin:
        return redirect('admin_dashboard')

    concerns = Concern.objects.filter(user=request.user).order_by('-date_submitted')
    form = ConcernForm()

    if request.method == 'POST':
        form = ConcernForm(request.POST, request.FILES)
        if form.is_valid():
            concern = form.save(commit=False)
            concern.user = request.user
            concern.save()
            messages.success(request, 'Concern submitted successfully!')
            return redirect('user_dashboard')

    notifications = concerns.all().annotate(
        status_order=Case(
            When(status='Pending', then=0),
            When(status='In Progress', then=1),
            When(status='Resolved', then=2),
            default=3,
            output_field=IntegerField(),
        )
    ).order_by('status_order', '-date_submitted')

    has_active_notif = concerns.filter(status__in=['Pending', 'In Progress', 'Resolved']).exists()
    pending_count = concerns.filter(status='Pending').count()
    inprogress_count = concerns.filter(status='In Progress').count()
    resolved_count = concerns.filter(status='Resolved').count()

    return render(request, 'tickets/user_dashboard.html', {
        'my_concerns': concerns,
        'form': form,
        'profile': profile,
        'subcategory_map': json.dumps(SUBCATEGORY_MAP),
        'notifications': notifications,
        'has_active_notif': has_active_notif,
        'pending_count': pending_count,
        'inprogress_count': inprogress_count,
        'resolved_count': resolved_count,
        'departments': DEPARTMENT_CHOICES,
        'categories': SUBCATEGORY_MAP,
    })


# ─────────────────────────────────────────
# SUBMIT CONCERN
# ─────────────────────────────────────────
@login_required
def submit_concern(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        sub_category = request.POST.get('sub_category')
        description = request.POST.get('description')
        attachment = request.FILES.get('attachment')

        if category and sub_category and description:
            concern = Concern(
                user=request.user,
                category=category,
                sub_category=sub_category,
                description=description,
            )
            if attachment:
                concern.attachment = attachment
            concern.save()
            messages.success(request, 'Your concern has been submitted successfully.')
        else:
            messages.error(request, 'Please fill in all required fields.')

    return redirect('user_dashboard')


# ─────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────
@login_required
def admin_dashboard(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if not profile.is_admin:
        return redirect('user_dashboard')

    selected_dept = request.GET.get('department', '')
    active_concerns = Concern.objects.exclude(status='Resolved').order_by('-date_submitted').select_related('user', 'user__userprofile')
    resolved_concerns = Concern.objects.filter(status='Resolved').order_by('-date_submitted').select_related('user', 'user__userprofile')
    concerns = list(active_concerns) + list(resolved_concerns)

    if selected_dept:
        active_concerns = Concern.objects.exclude(status='Resolved').filter(
            user__userprofile__department=selected_dept
        ).order_by('-date_submitted').select_related('user', 'user__userprofile')
        resolved_concerns = Concern.objects.filter(
            status='Resolved',
            user__userprofile__department=selected_dept
        ).order_by('-date_submitted').select_related('user', 'user__userprofile')
        concerns = list(active_concerns) + list(resolved_concerns)

    total = Concern.objects.count()
    pending = Concern.objects.filter(status='Pending').count()
    progress = Concern.objects.filter(status='In Progress').count()
    resolved = Concern.objects.filter(status='Resolved').count()
    unread_messages = Message.objects.filter(is_read=False).count()

    dept_counts = dict(
    Concern.objects.exclude(status='Resolved')
                   .values_list('user__userprofile__department')
                   .annotate(count=Count('id'))
)

    inbox_msgs = Message.objects.order_by('-date_sent').select_related('sender')
    inbox_messages_json = json.dumps([
        {
            'id': m.sender.id,
            'name': m.sender.get_full_name() or m.sender.username,
            'initials': (m.sender.get_full_name() or m.sender.username)[:2].upper(),
            'preview': m.subject,
            'unread': not m.is_read,
            'messages': [{'from': 'user', 'text': m.body, 'time': m.date_sent.strftime('%b %d, %I:%M %p')}]
        }
        for m in inbox_msgs
    ])

    return render(request, 'tickets/admin_dashboard.html', {
        'concerns': concerns,
        'profile': profile,
        'departments': DEPARTMENT_CHOICES,
        'selected_dept': selected_dept,
        'total': total,
        'pending': pending,
        'progress': progress,
        'resolved': resolved,
        'unread_messages': unread_messages,
        'dept_counts': dept_counts,
        'inbox_messages_json': inbox_messages_json,
    })


# ─────────────────────────────────────────
# UPDATE CONCERN STATUS (admin only)
# ─────────────────────────────────────────
@login_required
def update_concern(request, concern_id):
    profile = get_object_or_404(UserProfile, user=request.user)

    if not profile.is_admin:
        return redirect('user_dashboard')

    concern = get_object_or_404(Concern, id=concern_id)

    if request.method == 'POST':
        concern.status      = request.POST.get('status', concern.status)
        concern.remarks     = request.POST.get('remarks', concern.remarks)
        concern.assigned_to = request.POST.get('assigned_to', concern.assigned_to)
        concern.save()
        messages.success(request, f'Concern #{concern.id} updated successfully.')

    return redirect('admin_dashboard')