from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from users.permissions import IsEducationOfficer

from .models import CourseClass, School, Term
from .serializers import CourseClassSerializer, SchoolSerializer, TermSerializer


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
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_destroy(self, instance):
        if instance.course_classes.exists():
            raise ValidationError(
                {"detail": "A term with classes cannot be deleted."}
            )

        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()


class CourseClassViewSet(viewsets.ModelViewSet):
    queryset = CourseClass.objects.filter(is_deleted=False)
    serializer_class = CourseClassSerializer
    permission_classes = [IsEducationOfficer]

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
