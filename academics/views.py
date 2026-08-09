from django.utils import timezone
from rest_framework import viewsets

from users.permissions import IsEducationOfficer

from .models import School, Term
from .serializers import SchoolSerializer, TermSerializer


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.filter(is_deleted=False)
    serializer_class = SchoolSerializer
    permission_classes = [IsEducationOfficer]

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()


class TermViewSet(viewsets.ModelViewSet):
    queryset = Term.objects.filter(is_deleted=False)
    serializer_class = TermSerializer
    permission_classes = [IsEducationOfficer]

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
        