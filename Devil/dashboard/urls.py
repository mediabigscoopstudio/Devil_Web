from django.urls import path
from .views import dashboard_login, dashboard_logout, dashboard_home, user_list, user_action, report_list

urlpatterns = [
    path('', dashboard_home, name='dashboard-home'),
    path('login/', dashboard_login, name='dashboard-login'),
    path('dashboard/login/', dashboard_login),
    path('logout/', dashboard_logout, name='dashboard-logout'),
    path('dashboard/logout/', dashboard_logout),
    path('users/', user_list, name='dashboard-users'),
    path('users/<uuid:pk>/<str:action_type>/', user_action, name='dashboard-user-action'),
    path('reports/', report_list, name='dashboard-reports'),
]
