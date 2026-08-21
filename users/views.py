from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsSuperUser
from users.serializers import (
    AdminUserCreateSerializer,
    CurrentUserSerializer,
)


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class AdminUserCreateView(generics.CreateAPIView):
    serializer_class = AdminUserCreateSerializer
    permission_classes = [IsSuperUser]