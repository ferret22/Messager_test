from django.urls import path

from .views import (
    ChatListAPIView, 
    MessageListCreateAPIView, 
    PrivateChatCreateAPIView, 
    GroupChatCreateAPIView, 
    ChatMemberListAPIView,
    ChatReadAPIView,
)


urlpatterns = [
    path('chats/', ChatListAPIView.as_view(), name='chat-list'),
    path('chats/<int:chat_id>/messages/', MessageListCreateAPIView.as_view(), name='message-list-create'),
    path('chats/private/', PrivateChatCreateAPIView.as_view(), name='private-chat-create'),
    path('chats/group/', GroupChatCreateAPIView.as_view(), name='group-chat-create'),
    path('chats/<int:chat_id>/members/', ChatMemberListAPIView.as_view(), name='chat-member-list'),
    path('chats/<int:chat_id>/read/', ChatReadAPIView.as_view(), name='chat-read'),
]
