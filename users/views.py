from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from users.permissions import IsSuperUser
from users.serializers import (
    AdminUserCreateSerializer,
    CurrentUserSerializer,
)
from users.throttles import LoginRateThrottle


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class AdminUserCreateView(generics.CreateAPIView):
    serializer_class = AdminUserCreateSerializer
    permission_classes = [IsSuperUser]


class LoginView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]