from rest_framework import serializers
from .models import Conversation, Message
from matching.serializers import MatchSerializer

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'message_type', 'text', 'is_read', 'created_at']
        read_only_fields = ['sender', 'conversation']

class ConversationSerializer(serializers.ModelSerializer):
    match = MatchSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'match', 'is_active', 'created_at', 'last_message']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
