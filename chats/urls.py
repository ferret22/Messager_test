from django.urls import path

from .views import ChatListAPIView


urlpatterns = [
    path('chats/', ChatListAPIView.as_view(), name='chat-list'),
]
