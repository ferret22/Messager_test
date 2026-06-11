from django.urls import path

from .views import ChatListAPIView, MessageListCreateAPIView, PrivateChatCreateAPIView


urlpatterns = [
    path('chats/', ChatListAPIView.as_view(), name='chat-list'),
    path('chats/<int:chat_id>/messages/', MessageListCreateAPIView.as_view(), name='message-list-create'),
    path('chats/private/', PrivateChatCreateAPIView.as_view(), name='private-chat-create'),
]
