from django.contrib.auth import get_user_model, authenticate, login, logout
from django.db.models import Q
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    CurrentUserSerializer,
    UserSearchSerializer,
    LoginSerializer,
)


User = get_user_model()


class CurrentUserAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)


class UserSearchAPIView(ListAPIView):
    serializer_class = UserSearchSerializer
    permission_classes = (permissions.IsAuthenticated, )
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '').strip()
        if not query:
            return User.objects.none()
        
        return User.objects.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        ).exclude(
            id=self.request.user.id,
        ).order_by('username')[:20]


class LoginAPIView(APIView):
    permission_classes = (permissions.AllowAny, )
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        
        if user is None:
            return Response(
                {'detail': 'Invalid username or password'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        login(request, user)
        return Response(CurrentUserSerializer(user).data)


class LogoutAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenAPIView(APIView):
    permission_classes = (permissions.AllowAny, )
    
    def get(self, request):
        return Response({'detail': 'CSRF cookie set'})
