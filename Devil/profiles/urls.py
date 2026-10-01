from django.urls import path
from .views import ProfileView, PhotoListCreateView, PhotoDetailView, InterestListView, UserInterestView, PreferenceView

urlpatterns = [
    path('', ProfileView.as_view(), name='profile'),
    path('photos/', PhotoListCreateView.as_view(), name='photo-list-create'),
    path('photos/<uuid:pk>/', PhotoDetailView.as_view(), name='photo-detail'),
    path('interests/all/', InterestListView.as_view(), name='interest-list'),
    path('interests/', UserInterestView.as_view(), name='user-interests'),
    path('preferences/', PreferenceView.as_view(), name='preferences'),
]
