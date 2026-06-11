# from django.shortcuts import render
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView, ListCreateAPIView, CreateAPIView
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Chat, Message, ChatMember
from .serializers import (ChatSerializer, MessageSerializer, 
                          MessageCreateSerializer, PrivateChatCreateSerializer)


User = get_user_model()

# Create your views here.
class ChatListAPIView(ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Chat.objects.filter(
            members__user=self.request.user,
        ).distinct()


class MessageListCreateAPIView(ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        return Message.objects.filter(
            chat_id=chat_id,
            chat__members__user=self.request.user,
        ).select_related('sender')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, request, *args, **kwargs):
        chat_id = self.kwargs['chat_id']
        is_member = Chat.objects.filter(
            id=chat_id,
            members__user=request.user,
        ).exists()
        
        if not is_member:
            return Response(
                {
                    'detail': 'You are not a member of this chat.'
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.save(
            chat_id=chat_id,
            sender=request.user,
        )
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


class PrivateChatCreateAPIView(CreateAPIView):
    serializer_class = PrivateChatCreateSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        other_user = User.objects.get(id=serializer.validated_data['user_id'])
        
        chat = Chat.objects.create(
            chat_type=Chat.ChatType.PRIVATE,
            title='',
        )
        
        ChatMember.objects.bulk_create([
            ChatMember(chat=chat, user=request.user),
            ChatMember(chat=chat, user=other_user),
        ])
        
        return Response(
            ChatSerializer(chat).data,
            status=status.HTTP_201_CREATED,
        )
