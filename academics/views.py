from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from users.permissions import IsEducationOfficer, IsEducationOfficerOrTeacher

from .filters import CourseClassFilter
from .models import (
    CourseClass,
    CourseSession,
    School,
    TeacherClassAssignment,
    Term,
)
from .serializers import (
    CourseClassDetailSerializer,
    CourseClassSerializer,
    CourseSessionSerializer,
    SchoolSerializer,
    TeacherClassAssignmentSerializer,
    TermSerializer,
)
from .services import filter_sessions_for_teacher


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.filter(is_deleted=False)
    serializer_class = SchoolSerializer
    permission_classes = [IsEducationOfficer]

    def perform_destroy(self, instance):
        if instance.course_classes.filter(is_deleted=False).exists():
            raise ValidationError(
                {"detail": "A school with active classes cannot be deleted."}
            )

        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

class TermViewSet(viewsets.ModelViewSet):
    queryset = Term.objects.filter(is_deleted=False)
    serializer_class = TermSerializer
    permission_classes = [IsEducationOfficer]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_destroy(self, instance):
        if instance.course_classes.filter(is_deleted=False).exists():
            raise ValidationError(
                {"detail": "A term with active classes cannot be deleted."}
            )

        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()


class CourseClassViewSet(viewsets.ModelViewSet):
    queryset = CourseClass.objects.filter(is_deleted=False)
    serializer_class = CourseClassSerializer
    permission_classes = [IsEducationOfficerOrTeacher]
    filterset_class = CourseClassFilter
    search_fields = [
        "school__name",
        "term__term_type",
        "teacher_assignments__teacher__first_name",
        "teacher_assignments__teacher__last_name",
    ]

    def get_queryset(self):
        queryset = CourseClass.objects.filter(is_deleted=False)

        if self.request.user.role == "teacher":
            return queryset.filter(
                teacher_assignments__teacher=self.request.user
            ).distinct()

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseClassDetailSerializer

        return CourseClassSerializer


    def perform_destroy(self, instance):
        if instance.has_reported_sessions():
            raise ValidationError(
                {
                    "detail": (
                        "Class cannot be deleted after a related report "
                        "has been submitted."
                    )
                }
            )

        if instance.sessions.filter(is_deleted=False).exists():
            raise ValidationError(
                {
                    "detail": (
                        "A class with active sessions cannot be deleted."
                    )
                }
            )

        if instance.teacher_assignments.exists():
            raise ValidationError(
                {
                    "detail": (
                        "A class with teacher assignments cannot be deleted."
                    )
                }
            )

        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

        
class TeacherClassAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TeacherClassAssignment.objects.all()
    serializer_class = TeacherClassAssignmentSerializer
    permission_classes = [IsEducationOfficer]

    def perform_destroy(self, instance):
        if instance.has_reported_sessions():
            raise ValidationError(
                {
                    "detail": (
                        "Assignment cannot be deleted after a related report "
                        "has been submitted."
                    )
                }
            )

        instance.delete()


class CourseSessionViewSet(viewsets.ModelViewSet):
    queryset = CourseSession.objects.filter(is_deleted=False)
    serializer_class = CourseSessionSerializer
    permission_classes = [IsEducationOfficerOrTeacher]

    def get_queryset(self):
        queryset = CourseSession.objects.filter(is_deleted=False)

        if self.request.user.role == "teacher":
            return filter_sessions_for_teacher(
                queryset,
                self.request.user.id,
            )

        return queryset

    def perform_destroy(self, instance):
        if instance.has_report():
            raise ValidationError(
                {
                    "detail": (
                        "Session cannot be deleted after a report has been submitted."
                    )
                }
            )

        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()