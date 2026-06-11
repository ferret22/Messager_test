from django.urls import path

from .views import ChatListAPIView, MessageListAPIView


urlpatterns = [
    path('chats/', ChatListAPIView.as_view(), name='chat-list'),
    path('chats/<int:chat_id>/messages/', MessageListAPIView.as_view(), name='message-list'),
]
