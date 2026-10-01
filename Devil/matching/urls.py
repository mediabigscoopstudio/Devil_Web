from django.urls import path
from .views import MatchListView, MatchDetailView

urlpatterns = [
    path('', MatchListView.as_view(), name='match-list'),
    path('<uuid:pk>/', MatchDetailView.as_view(), name='match-detail'),
]
