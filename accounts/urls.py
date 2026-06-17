from django.urls import path

from .views import (
    CurrentUserAPIView,
    UserSearchAPIView,
)


urlpatterns = [
    path('me/', CurrentUserAPIView.as_view(), name='current-user'),
    path('users/search/', UserSearchAPIView.as_view(), name='user-search'),
]
