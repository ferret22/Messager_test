# from django.shortcuts import render
from rest_framework import permissions
from rest_framework.generics import ListAPIView

from .models import Chat
from .serializers import ChatSerializer

# Create your views here.
class ChatListAPIView(ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Chat.objects.filter(
            members__user=self.request.user,
        ).distinct()
