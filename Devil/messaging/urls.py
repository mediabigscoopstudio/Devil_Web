from django.urls import path
from .views import ConversationListView, ConversationDetailView, MessageListCreateView, MarkMessageReadView

urlpatterns = [
    path('', ConversationListView.as_view(), name='conversation-list'),
    path('<uuid:pk>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('<uuid:conversation_id>/messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<uuid:pk>/read/', MarkMessageReadView.as_view(), name='message-read'),
]
