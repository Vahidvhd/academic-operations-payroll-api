from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .serializers import CurrentUserSerializer


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user