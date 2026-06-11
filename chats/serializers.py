from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Chat, ChatMember, Message


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
        prefetched_messages = list(obj.messages.all())
        
        if prefetched_messages:
            message = prefetched_messages[0]
        else:
            message = obj.messages.order_by('-created_at').select_related('sender').first()
        
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


class GroupChatCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )
    
    def validate_member_ids(self, value):
        request_user = self.context['request'].user
        unique_member_ids = set(value)
        
        if request_user.id in unique_member_ids:
            raise serializers.ValidationError('Do not include yourself in member_ids.')
        
        existing_users_count = User.objects.filter(
            id__in=unique_member_ids,
        ).count()
        
        if existing_users_count != len(unique_member_ids):
            raise serializers.ValidationError('One or more users do not exist.')
        
        return list(unique_member_ids)


class ChatMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='user.username',
        read_only=True,
    )
    
    class Meta:
        model = ChatMember
        fields = (
            'id',
            'user',
            'username',
            'last_read_message',
            'joined_at',
        )
