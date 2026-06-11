from email import message

from rest_framework import serializers
from .models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(
        source="sender.username",
        read_only=True,
    )
    
    class Meta:
        model = Message
        fields = (
            'id',
            'sender',
            'sender_username',
            'text',
            'created_at',
            'edited_at',
        )


class ChatSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = (
            'id',
            'title',
            'chat_type',
            'created_at',
            'last_message',
        )
    
    def get_last_message(self, obj):
        message = obj.messages.order_by('-created_at').first()
        
        if message is None:
            return None
        return MessageSerializer(message).data


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('text',)
