from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

class ConversationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(
            Q(match__user_one=request.user) | Q(match__user_two=request.user),
            is_active=True
        ).order_by('-updated_at')
        return Response(ConversationSerializer(conversations, many=True, context={'request': request}).data)

class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            conversation = Conversation.objects.get(
                Q(match__user_one=request.user) | Q(match__user_two=request.user),
                id=pk,
                is_active=True
            )
            return Response(ConversationSerializer(conversation, context={'request': request}).data)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

class MessageListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                Q(match__user_one=request.user) | Q(match__user_two=request.user),
                id=conversation_id
            )
            messages = conversation.messages.order_by('created_at')
            return Response(MessageSerializer(messages, many=True).data)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                Q(match__user_one=request.user) | Q(match__user_two=request.user),
                id=conversation_id,
                is_active=True
            )
            text = request.data.get('text')
            if not text:
                return Response({'error': 'Message text is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                text=text
            )
            conversation.save() # updates updated_at
            return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

class MarkMessageReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            msg = Message.objects.get(id=pk)
            if msg.conversation.match.user_one == request.user or msg.conversation.match.user_two == request.user:
                msg.is_read = True
                msg.save()
                return Response({'status': 'marked as read'})
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
