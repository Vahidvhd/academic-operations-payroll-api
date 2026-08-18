from django.db.models import F, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from reports.models import SessionReport
from reports.serializers import SessionReportReviewSerializer, SessionReportSerializer
from users.permissions import (
    IsEducationOfficer,
    IsEducationOfficerOrTeacher,
    IsTeacher,
)


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

        if self.action == "review":
            return [IsEducationOfficer()]

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

    def partial_update(self, request, *args, **kwargs):
        report = self.get_object()

        if report.status != SessionReport.Status.REJECTED:
            raise ValidationError(
                {"detail": "Only rejected reports can be edited."}
            )

        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        report = self.get_object()

        if report.status == SessionReport.Status.APPROVED:
            raise ValidationError(
                {"detail": "Approved reports cannot be reviewed again."}
            )

        serializer = SessionReportReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]

        if (
            report.status == SessionReport.Status.REJECTED
            and new_status != SessionReport.Status.APPROVED
        ):
            raise ValidationError(
                {"detail": "A rejected report can only be approved or resubmitted by the teacher."}
            )

        report.status = new_status
        report.review_note = serializer.validated_data.get("review_note", "")
        report.reviewed_by = request.user

        if new_status == SessionReport.Status.APPROVED:
            report.late_hours = report.calculate_late_hours(timezone.now())

        report.save()

        return Response(SessionReportSerializer(report).data)