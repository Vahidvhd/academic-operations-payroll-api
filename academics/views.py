from django.db.models import F, Q
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
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

        
class TeacherClassAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TeacherClassAssignment.objects.all()
    serializer_class = TeacherClassAssignmentSerializer
    permission_classes = [IsEducationOfficer]


class CourseSessionViewSet(viewsets.ModelViewSet):
    queryset = CourseSession.objects.filter(is_deleted=False)
    serializer_class = CourseSessionSerializer
    permission_classes = [IsEducationOfficerOrTeacher]

    def get_queryset(self):
        queryset = CourseSession.objects.filter(is_deleted=False)

        if self.request.user.role == "teacher":
            return queryset.filter(
                Q(conducted_by=self.request.user)
                | (
                    Q(conducted_by__isnull=True)
                    & Q(
                        course_class__teacher_assignments__teacher=self.request.user
                    )
                    & Q(
                        session_datetime__date__gte=F(
                            "course_class__teacher_assignments__start_date"
                        )
                    )
                    & (
                        Q(
                            course_class__teacher_assignments__end_date__isnull=True
                        )
                        | Q(
                            session_datetime__date__lte=F(
                                "course_class__teacher_assignments__end_date"
                            )
                        )
                    )
                )
            ).distinct()

        return queryset

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()