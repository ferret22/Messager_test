# from django.shortcuts import render
from rest_framework import permissions
from rest_framework.generics import ListAPIView

from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer


# Create your views here.
class ChatListAPIView(ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Chat.objects.filter(
            members__user=self.request.user,
        ).distinct()


class MessageListAPIView(ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        return Message.objects.filter(
            chat_id=chat_id,
            chat__members__user=self.request.user,
        ).select_related('sender')
