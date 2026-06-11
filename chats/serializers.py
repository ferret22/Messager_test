from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Chat, Message


User = get_user_model()


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
    display_title = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = (
            'id',
            'title',
            'display_title',
            'chat_type',
            'created_at',
            'last_message',
        )
    
    def get_display_title(self, obj):
        if obj.chat_type != Chat.ChatType.PRIVATE:
            return obj.title
        
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return obj.title
        
        other_member = obj.members.exclude(
            user=request.user,
        ).select_related('user').first()
        
        if other_member is None:
            return obj.title
        
        return other_member.user.username
    
    def get_last_message(self, obj):
        message = obj.messages.order_by('-created_at').first()
        
        if message is None:
            return None
        return MessageSerializer(message).data


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('text',)


class PrivateChatCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        request_user = self.context['request'].user
        
        if value == request_user.id:
            raise serializers.ValidationError('You cannot create a private chat with yourself.')

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('User does not exist.')

        return value
