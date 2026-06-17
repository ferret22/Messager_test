from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    CurrentUserSerializer,
    UserSearchSerializer,
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
