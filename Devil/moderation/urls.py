from django.urls import path
from .views import BlockListCreateView, BlockDetailView, ReportListCreateView

urlpatterns = [
    path('blocks/', BlockListCreateView.as_view(), name='block-list-create'),
    path('blocks/<uuid:user_id>/', BlockDetailView.as_view(), name='block-detail'),
    path('reports/', ReportListCreateView.as_view(), name='report-list-create'),
]
