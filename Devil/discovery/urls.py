from django.urls import path
from .views import DiscoveryFeedView, SwipeView

urlpatterns = [
    path('', DiscoveryFeedView.as_view(), name='discovery-feed'),
    path('swipe/', SwipeView.as_view(), name='swipe'),
]
