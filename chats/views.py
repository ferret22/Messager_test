from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from django.db import transaction
from django.db.models import Prefetch
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.generics import (
    ListAPIView, 
    ListCreateAPIView, 
    CreateAPIView,
    RetrieveUpdateDestroyAPIView,
)

from .models import (Chat, Message, ChatMember, MessageDeletion)
from .serializers import (
    ChatSerializer, 
    MessageSerializer, 
    MessageCreateSerializer, 
    PrivateChatCreateSerializer, 
    GroupChatCreateSerializer, 
    ChatMemberSerializer,
    ChatReadSerializer,
    MessageUpdateSerializer,
)


User = get_user_model()


def send_chat_event(chat_id, event):
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        f'chat_{chat_id}',
        event,
    )


def send_chat_event(user_id, event):
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        event,
    )


# Create your views here.
class ChatListAPIView(ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Chat.objects.filter(
            members__user=self.request.user,
        ).prefetch_related(
            Prefetch(
                'members',
                queryset=ChatMember.objects.select_related('user'),
            ),
            Prefetch(
              'messages',
              queryset=Message.objects.select_related('sender').order_by('-created_at'),
            ),
        ).distinct()


class MessageListCreateAPIView(ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_chat(self):
        return get_object_or_404(
            Chat,
            id=self.kwargs['chat_id'],
            members__user=self.request.user,
        )
    
    def get_queryset(self):
        chat = self.get_chat()
        
        return Message.objects.filter(
            chat=chat,
            is_deleted=False,
        ).exclude(
            deletions__user=self.request.user,
        ).select_related('sender')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, request, *args, **kwargs):
        chat = self.get_chat()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.save(
            chat=chat,
            sender=request.user,
        )
        
        return Response(
            MessageSerializer(
                message,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class PrivateChatCreateAPIView(CreateAPIView):
    serializer_class = PrivateChatCreateSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        other_user = serializer.validated_data['other_user']
        
        existing_chat = Chat.objects.filter(
            chat_type=Chat.ChatType.PRIVATE,
            members__user=request.user,
        ).filter(
            members__user=other_user,
        ).first()
        
        if existing_chat is not None:
            return Response(
                ChatSerializer(existing_chat, context={'request': request}).data,
                status=status.HTTP_200_OK,
            )
        
        chat = Chat.objects.create(
            chat_type=Chat.ChatType.PRIVATE,
            title='',
        )
        
        ChatMember.objects.bulk_create([
            ChatMember(chat=chat, user=request.user),
            ChatMember(chat=chat, user=other_user),
        ])
        
        return Response(
            ChatSerializer(chat, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class GroupChatCreateAPIView(CreateAPIView):
    serializer_class = GroupChatCreateSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        member_ids = serializer.validated_data['member_ids']
        members = list(User.objects.filter(id__in=member_ids))
        
        chat = Chat.objects.create(
            chat_type=Chat.ChatType.GROUP,
            title=serializer.validated_data['title'],
        )
        
        chat_members = [
            ChatMember(chat=chat, user=request.user),
        ]
        
        chat_members.extend(
            ChatMember(chat=chat, user=user) for user in members
        )
        
        ChatMember.objects.bulk_create(chat_members)
        
        return Response(
            ChatSerializer(
                chat,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class ChatMemberListAPIView(ListAPIView):
    serializer_class = ChatMemberSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_chat(self):
        return get_object_or_404(
            Chat,
            id=self.kwargs['chat_id'],
            members__user=self.request.user,
        )
    
    def get_queryset(self):
        chat = self.get_chat()
        
        return ChatMember.objects.filter(
            chat=chat,
        ).select_related('user')


class ChatReadAPIView(CreateAPIView):
    serializer_class = ChatReadSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_chat_member(self):
        return get_object_or_404(
            ChatMember,
            chat_id=self.kwargs['chat_id'],
            user=self.request.user,
        )
    
    def create(self, request, *args, **kwargs):
        chat_member = self.get_chat_member()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = get_object_or_404(
            Message,
            id=serializer.validated_data['message_id'],
            chat_id=self.kwargs['chat_id'],
        )
        
        chat_member.last_read_message = message
        chat_member.save(update_fields=['last_read_message'])
        
        send_chat_event(
            chat_member.chat_id,
            {
                'type': 'read.updated',
                'read': {
                    'chat_id': chat_member.chat_id,
                    'user': request.user.id,
                    'username': request.user.username,
                    'last_read_message': message.id,
                },
            },
        )
        
        return Response(
            ChatMemberSerializer(chat_member).data,
            status=status.HTTP_200_OK,
        )


class ChatReadAllAPIView(CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_chat_member(self):
        return get_object_or_404(
            ChatMember,
            chat_id=self.kwargs['chat_id'],
            user=self.request.user,
        )
    
    def create(self, request, *args, **kwargs):
        chat_member = self.get_chat_member()
        
        last_message = Message.objects.filter(
            chat=chat_member.chat,
        ).order_by('-created_at').first()
        
        chat_member.last_read_message = last_message
        chat_member.save(update_fields=['last_read_message'])
        
        send_chat_event(
            chat_member.chat_id,
            {
                'type': 'read.updated',
                'read': {
                    'chat_id': chat_member.chat_id,
                    'user': request.user.id,
                    'username': request.user.username,
                    'last_read_message': last_message.id if last_message else None,
                },
            },
        )
        
        return Response(
            ChatMemberSerializer(chat_member).data,
            status=status.HTTP_200_OK,
        )


class MessageDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return Message.objects.filter(
            chat__members__user=self.request.user,
        ).select_related('sender', 'chat')

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return MessageUpdateSerializer
        
        return MessageSerializer
    
    def perform_update(self, serializer):
        message = self.get_object()
        
        if message.sender_id != self.request.user.id:
            raise PermissionDenied('You can edit only your own messages.')
        
        if message.is_deleted:
            raise PermissionDenied('You cannot edit a delete message.')

        message = serializer.save(edited_at=timezone.now())
        
        send_chat_event(
            message.chat_id,
            {
              'type': 'message.updated',
              'message': {
                    'id': message.id,
                    'text': message.text,
                    'edited_at': message.edited_at.isoformat(),
              },
            },
        )
    
    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        delete_for_everyone = request.data.get('delete_for_everyone', False)
        
        if delete_for_everyone:
            if message.sender_id != request.user.id:
                raise PermissionDenied('You can delete for everyone only your own messages.')

            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.save(update_fields=['is_deleted', 'deleted_at'])
            
            send_chat_event(
                message.chat_id,
                {
                    'type': 'message.deleted',
                    'message': {
                        'id': message.id,
                        'deleted_for_everyone': True,
                    },  
                },
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        MessageDeletion.objects.get_or_create(
            message=message,
            user=request.user,
        )
        
        send_user_event(
            request.user.id,
            {
                'type': 'message.deleted',
                'message': {
                    'id': message.id,
                    'deleted_for_everyone': False,
                },  
            },
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # def perform_destroy(self, instance):
    #     if instance.sender_id != self.request.user.id:
    #         raise PermissionDenied('You can delete only your own messages.')
        
    #     instance.delete()
