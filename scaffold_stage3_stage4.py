import os

base_dir = '/Volumes/Juggernut_Assist/Projects/Devil/Devil_web/Devil'

# 1. MODERATION VIEWS & SERIALIZERS
moderation_serializers = '''from rest_framework import serializers
from .models import Block, Report, ModerationAction

class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ['id', 'blocker', 'blocked', 'created_at']
        read_only_fields = ['blocker']

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'reporter', 'reported_user', 'reason', 'description', 'status', 'created_at']
        read_only_fields = ['reporter', 'status']
'''

moderation_views = '''from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Block, Report
from accounts.models import User
from .serializers import BlockSerializer, ReportSerializer

class BlockListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        blocks = Block.objects.filter(blocker=request.user)
        return Response(BlockSerializer(blocks, many=True).data)

    def post(self, request):
        blocked_user_id = request.data.get('blocked_user_id')
        if not blocked_user_id:
            return Response({'error': 'blocked_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            blocked_user = User.objects.get(id=blocked_user_id)
            block, _ = Block.objects.get_or_create(blocker=request.user, blocked=blocked_user)
            return Response(BlockSerializer(block).data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class BlockDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, user_id):
        Block.objects.filter(blocker=request.user, blocked_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ReportListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        reports = Report.objects.filter(reporter=request.user)
        return Response(ReportSerializer(reports, many=True).data)

    def post(self, request):
        reported_user_id = request.data.get('reported_user_id')
        reason = request.data.get('reason')
        description = request.data.get('description', '')

        if not reported_user_id or not reason:
            return Response({'error': 'reported_user_id and reason are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reported_user = User.objects.get(id=reported_user_id)
            report = Report.objects.create(
                reporter=request.user,
                reported_user=reported_user,
                reason=reason,
                description=description
            )
            return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
'''

moderation_urls = '''from django.urls import path
from .views import BlockListCreateView, BlockDetailView, ReportListCreateView

urlpatterns = [
    path('blocks/', BlockListCreateView.as_view(), name='block-list-create'),
    path('blocks/<uuid:user_id>/', BlockDetailView.as_view(), name='block-detail'),
    path('reports/', ReportListCreateView.as_view(), name='report-list-create'),
]
'''

# 2. NOTIFICATIONS VIEWS & SERIALIZERS
notifications_serializers = '''from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'body', 'is_read', 'created_at']
'''

notifications_views = '''from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        return Response(NotificationSerializer(notifications, many=True).data)

class NotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            notif = Notification.objects.get(id=pk, user=request.user)
            notif.is_read = True
            notif.save()
            return Response(NotificationSerializer(notif).data)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

class NotificationReadAllView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})
'''

notifications_urls = '''from django.urls import path
from .views import NotificationListView, NotificationReadView, NotificationReadAllView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<uuid:pk>/read/', NotificationReadView.as_view(), name='notification-read'),
    path('read-all/', NotificationReadAllView.as_view(), name='notification-read-all'),
]
'''

# 3. SUPER ADMIN DASHBOARD VIEWS & TEMPLATES
dashboard_views = '''from django.shortcuts import render, redirect, get_object_or_404
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
        phone = request.POST.get('phone_number')
        password = request.POST.get('password')
        user = authenticate(request, username=phone, password=password)
        if user and user.is_superuser:
            login(request, user)
            return redirect('dashboard-home')
        else:
            messages.error(request, 'Invalid credentials or non-superuser account.')
    return render(request, 'dashboard/login.html')

@superuser_required
def dashboard_logout(request):
    logout(request)
    return redirect('dashboard-login')

@superuser_required
def dashboard_home(request):
    context = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(status='ACTIVE').count(),
        'suspended_users': User.objects.filter(status='SUSPENDED').count(),
        'banned_users': User.objects.filter(status='BANNED').count(),
        'total_matches': Match.objects.count(),
        'total_messages': Message.objects.count(),
        'open_reports': Report.objects.filter(status='OPEN').count(),
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
'''

dashboard_urls = '''from django.urls import path
from .views import dashboard_login, dashboard_logout, dashboard_home, user_list, user_action, report_list

urlpatterns = [
    path('', dashboard_home, name='dashboard-home'),
    path('login/', dashboard_login, name='dashboard-login'),
    path('logout/', dashboard_logout, name='dashboard-logout'),
    path('users/', user_list, name='dashboard-users'),
    path('users/<uuid:pk>/<str:action_type>/', user_action, name='dashboard-user-action'),
    path('reports/', report_list, name='dashboard-reports'),
]
'''

# Templates directory setup
templates_dir = '/Volumes/Juggernut_Assist/Projects/Devil/Devil_web/Devil/templates/dashboard'
os.makedirs(templates_dir, exist_ok=True)

base_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Devil Super Admin Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body { background-color: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .sidebar { min-height: 100vh; background: #1a1d20; color: #fff; }
        .sidebar a { color: #ced4da; text-decoration: none; padding: 10px 15px; display: block; border-radius: 4px; }
        .sidebar a:hover, .sidebar a.active { background: #343a40; color: #fff; }
        .stat-card { border-radius: 8px; border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
</head>
<body>
    <div class="d-flex">
        <div class="sidebar p-3 style="width: 250px;">
            <h4 class="text-white mb-4">Devil Admin</h4>
            <nav>
                <a href="{% url 'dashboard-home' %}" class="mb-2">Overview</a>
                <a href="{% url 'dashboard-users' %}" class="mb-2">User Management</a>
                <a href="{% url 'dashboard-reports' %}" class="mb-2">Reports & Moderation</a>
                <a href="{% url 'dashboard-logout' %}" class="mt-4 text-danger">Logout</a>
            </nav>
        </div>
        <div class="flex-grow-1 p-4">
            {% block content %}{% endblock %}
        </div>
    </div>
</body>
</html>
'''

login_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Super Admin Login | Devil</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-light d-flex align-items-center justify-content-center" style="height: 100vh;">
    <div class="card p-4 shadow-sm" style="width: 350px;">
        <h3 class="card-title text-center mb-4">Devil Admin Login</h3>
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-danger p-2 text-center" style="font-size: 14px;">{{ message }}</div>
            {% endfor %}
        {% endif %}
        <form method="POST">
            {% csrf_token %}
            <div class="mb-3">
                <label class="form-label">Phone Number</label>
                <input type="text" name="phone_number" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-dark w-100">Sign In</button>
        </form>
    </div>
</body>
</html>
'''

home_html = '''{% extends "dashboard/base.html" %}
{% block content %}
<h2>System Overview</h2>
<div class="row g-3 mt-3">
    <div class="col-md-3">
        <div class="card p-3 stat-card bg-white">
            <small class="text-muted">Total Users</small>
            <h3>{{ total_users }}</h3>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3 stat-card bg-white">
            <small class="text-muted">Active Users</small>
            <h3 class="text-success">{{ active_users }}</h3>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3 stat-card bg-white">
            <small class="text-muted">Total Matches</small>
            <h3 class="text-primary">{{ total_matches }}</h3>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3 stat-card bg-white">
            <small class="text-muted">Open Reports</small>
            <h3 class="text-danger">{{ open_reports }}</h3>
        </div>
    </div>
</div>
{% endblock %}
'''

users_html = '''{% extends "dashboard/base.html" %}
{% block content %}
<h2>User Management</h2>
<table class="table table-striped mt-3">
    <thead>
        <tr>
            <th>ID</th><th>Phone</th><th>Status</th><th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for u in users %}
        <tr>
            <td>{{ u.id }}</td>
            <td>{{ u.phone_number }}</td>
            <td><span class="badge bg-secondary">{{ u.status }}</span></td>
            <td>
                {% if u.status == 'ACTIVE' %}
                <a href="{% url 'dashboard-user-action' u.id 'suspend' %}" class="btn btn-sm btn-warning">Suspend</a>
                <a href="{% url 'dashboard-user-action' u.id 'ban' %}" class="btn btn-sm btn-danger">Ban</a>
                {% else %}
                <a href="{% url 'dashboard-user-action' u.id 'unban' %}" class="btn btn-sm btn-success">Unban</a>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
'''

reports_html = '''{% extends "dashboard/base.html" %}
{% block content %}
<h2>User Reports</h2>
<table class="table table-striped mt-3">
    <thead>
        <tr>
            <th>Reporter</th><th>Reported User</th><th>Reason</th><th>Status</th>
        </tr>
    </thead>
    <tbody>
        {% for r in reports %}
        <tr>
            <td>{{ r.reporter.phone_number }}</td>
            <td>{{ r.reported_user.phone_number }}</td>
            <td>{{ r.reason }}</td>
            <td><span class="badge bg-info">{{ r.status }}</span></td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
'''

with open(os.path.join(templates_dir, 'base.html'), 'w') as f: f.write(base_html)
with open(os.path.join(templates_dir, 'login.html'), 'w') as f: f.write(login_html)
with open(os.path.join(templates_dir, 'home.html'), 'w') as f: f.write(home_html)
with open(os.path.join(templates_dir, 'users.html'), 'w') as f: f.write(users_html)
with open(os.path.join(templates_dir, 'reports.html'), 'w') as f: f.write(reports_html)

# 4. CELERY SETUP
celery_py = '''import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Devil.settings')

app = Celery('Devil')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
'''

with open(os.path.join(base_dir, 'Devil', 'celery.py'), 'w') as f:
    f.write(celery_py)

# Write apps files
files_to_write = {
    'moderation/serializers.py': moderation_serializers,
    'moderation/views.py': moderation_views,
    'moderation/urls.py': moderation_urls,
    
    'notifications/serializers.py': notifications_serializers,
    'notifications/views.py': notifications_views,
    'notifications/urls.py': notifications_urls,
    
    'dashboard/views.py': dashboard_views,
    'dashboard/urls.py': dashboard_urls,
}

for rel_path, content in files_to_write.items():
    full_path = os.path.join(base_dir, rel_path)
    with open(full_path, 'w') as f:
        f.write(content)

# Update main urls.py
main_urls = '''from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/profile/', include('profiles.urls')),
    path('api/v1/discovery/', include('discovery.urls')),
    path('api/v1/matches/', include('matching.urls')),
    path('api/v1/conversations/', include('messaging.urls')),
    path('api/v1/moderation/', include('moderation.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
]
'''

with open(os.path.join(base_dir, 'Devil', 'urls.py'), 'w') as f:
    f.write(main_urls)

print("Stage 3 & 4 (Moderation, Dashboard, Notifications, Celery) scaffolded successfully.")
