from django.urls import path
from .views import (
    ProfileMeView, ProfileLocationView, ProfileNotificationPreferenceView,
    ProfileCompleteView, PhotoListCreateView, PhotoDetailView
)

urlpatterns = [
    path('me/', ProfileMeView.as_view(), name='profile-me'),
    path('location/', ProfileLocationView.as_view(), name='profile-location'),
    path('notification-preference/', ProfileNotificationPreferenceView.as_view(), name='profile-notifications'),
    path('complete/', ProfileCompleteView.as_view(), name='profile-complete'),
    path('photos/', PhotoListCreateView.as_view(), name='photo-list-create'),
    path('photos/<uuid:pk>/', PhotoDetailView.as_view(), name='photo-detail'),
]
