from django.urls import path

from .views import (
    CurrentUserAPIView,
    UserSearchAPIView,
    LoginAPIView,
    LogoutAPIView,
)


urlpatterns = [
    path('me/', CurrentUserAPIView.as_view(), name='current-user'),
    path('users/search/', UserSearchAPIView.as_view(), name='user-search'),
    path('auth/login/', LoginAPIView.as_view(), name='login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='logout'),
]
