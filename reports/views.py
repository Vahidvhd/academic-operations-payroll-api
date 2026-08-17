from django.db.models import F, Q
from rest_framework import viewsets

from reports.models import SessionReport
from reports.serializers import SessionReportSerializer
from users.permissions import IsEducationOfficerOrTeacher, IsTeacher


class SessionReportViewSet(viewsets.ModelViewSet):
    queryset = SessionReport.objects.all()
    serializer_class = SessionReportSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [IsTeacher()]

        if self.action in ["list", "retrieve"]:
            return [IsEducationOfficerOrTeacher()]

        if self.action == "partial_update":
            return [IsTeacher()]

        return super().get_permissions()

    def get_queryset(self):
        queryset = SessionReport.objects.all()

        if self.request.user.role == "teacher":
            return queryset.filter(
                Q(
                    session__course_class__teacher_assignments__end_date__isnull=True
                )
                | Q(
                    session__session_datetime__date__lte=F(
                        "session__course_class__teacher_assignments__end_date"
                    )
                ),
                session__course_class__teacher_assignments__teacher=self.request.user,
                session__session_datetime__date__gte=F(
                    "session__course_class__teacher_assignments__start_date"
                ),
            ).distinct()

        return queryset