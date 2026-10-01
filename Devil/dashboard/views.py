from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from accounts.models import User
from profiles.models import Profile, ProfilePhoto
from matching.models import Match
from messaging.models import Message
from moderation.models import Report, ModerationAction

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='/dashboard/login/')(view_func)

def dashboard_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('dashboard-home')
    
    if request.method == 'POST':
        login_input = request.POST.get('phone_number') or request.POST.get('login_input')
        password = request.POST.get('password')
        
        # Try finding by phone or email
        user_obj = User.objects.filter(phone_number=login_input).first() or User.objects.filter(email=login_input).first()
        if user_obj:
            user = authenticate(request, username=user_obj.phone_number, password=password)
            if user and user.is_superuser:
                login(request, user)
                return redirect('dashboard-home')
        
        messages.error(request, 'Invalid credentials or non-superuser account.')
    return render(request, 'dashboard/login.html')

@superuser_required
def dashboard_logout(request):
    logout(request)
    return redirect('dashboard-login')

@superuser_required
def dashboard_home(request):
    admin_name = getattr(request.user, 'profile', None) and request.user.profile.display_name or "Ketan"
    context = {
        'admin_name': admin_name,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(status='ACTIVE').count(),
        'suspended_users': User.objects.filter(status='SUSPENDED').count(),
        'banned_users': User.objects.filter(status='BANNED').count(),
        'total_matches': Match.objects.count(),
        'total_messages': Message.objects.count(),
        'open_reports': Report.objects.filter(status='OPEN').count(),
        'recent_users': User.objects.select_related('profile').order_by('-created_at')[:5],
        'recent_reports': Report.objects.select_related('reporter', 'reported_user').order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/home.html', context)

@superuser_required
def user_list(request):
    query = request.GET.get('q', '')
    users = User.objects.all().order_by('-created_at')
    if query:
        users = users.filter(phone_number__icontains=query)
    return render(request, 'dashboard/users.html', {'users': users, 'query': query})

@superuser_required
def user_action(request, pk, action_type):
    target_user = get_object_or_404(User, id=pk)
    if action_type == 'suspend':
        target_user.status = 'SUSPENDED'
        target_user.save()
        ModerationAction.objects.create(admin_user=request.user, target_user=target_user, action='USER_SUSPENDED')
    elif action_type == 'ban':
        target_user.status = 'BANNED'
        target_user.save()
        ModerationAction.objects.create(admin_user=request.user, target_user=target_user, action='USER_BANNED')
    elif action_type == 'unban':
        target_user.status = 'ACTIVE'
        target_user.save()
        ModerationAction.objects.create(admin_user=request.user, target_user=target_user, action='USER_UNBANNED')
    return redirect('dashboard-users')

@superuser_required
def report_list(request):
    reports = Report.objects.all().order_by('-created_at')
    return render(request, 'dashboard/reports.html', {'reports': reports})
