from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from academics.models import CourseSession
from academics.services import filter_sessions_for_teacher
from reports.filters import SessionReportFilter
from reports.models import ReportStatusHistory, SessionReport
from reports.serializers import (
    BulkReportApprovalSerializer,
    MonthlyReportSummaryQuerySerializer,
    ReportStatusHistorySerializer,
    SessionReportReviewSerializer,
    SessionReportSerializer,
)
from users.permissions import (
    IsEducationOfficer,
    IsEducationOfficerOrTeacher,
    IsTeacher,
)


class SessionReportViewSet(viewsets.ModelViewSet):
    queryset = SessionReport.objects.all()
    serializer_class = SessionReportSerializer
    filterset_class = SessionReportFilter
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

        if self.action == "history":
            return [IsEducationOfficer()]

        if self.action == "monthly_summary":
            return [IsTeacher()]

        if self.action == "bulk_approve":
            return [IsEducationOfficer()]

        return super().get_permissions()

    def get_queryset(self):
        queryset = SessionReport.objects.all()

        if self.request.user.role == "teacher":
            teacher_sessions = filter_sessions_for_teacher(
                CourseSession.objects.all(),
                self.request.user.id,
            )

            return queryset.filter(
                session__in=teacher_sessions
            )

        return queryset

    def filter_queryset(self, queryset):
        if (self.action == "list" and self.request.user.role == "education_officer"):
            return super().filter_queryset(queryset)

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
        old_status = report.status

        if (
            report.status == SessionReport.Status.REJECTED
            and new_status != SessionReport.Status.APPROVED
        ):
            raise ValidationError(
                {"detail": "A rejected report can only be approved or resubmitted by the teacher."}
            )
        

        with transaction.atomic():
            report.status = new_status
            report.review_note = serializer.validated_data.get("review_note", "")
            report.reviewed_by = request.user

            if new_status == SessionReport.Status.APPROVED:
                report.late_hours = report.calculate_late_hours(timezone.now())

            report.save()

            ReportStatusHistory.objects.create(
                session_report=report,
                changed_by=request.user,
                old_status=old_status,
                new_status=new_status,
                note=report.review_note,
            )

        return Response(SessionReportSerializer(report).data)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        report = self.get_object()

        histories = ReportStatusHistory.objects.filter(
            session_report=report
        ).order_by("created_at")

        serializer = ReportStatusHistorySerializer(
            histories,
            many=True,
        )

        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="monthly-summary")
    def monthly_summary(self, request):
        query_serializer = MonthlyReportSummaryQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)

        year = query_serializer.validated_data["year"]
        month = query_serializer.validated_data["month"]

        reports = self.get_queryset().filter(
            session__session_datetime__year=year,
            session__session_datetime__month=month,
        )

        summary = reports.aggregate(
            pending=Count(
                "id",
                filter=Q(status=SessionReport.Status.PENDING),
            ),
            approved=Count(
                "id",
                filter=Q(status=SessionReport.Status.APPROVED),
            ),
            rejected=Count(
                "id",
                filter=Q(status=SessionReport.Status.REJECTED),
            ),
            total=Count("id"),
        )

        return Response(
            {
                "year": year,
                "month": month,
                **summary,
            }
        )

    @action(detail=False, methods=["post"], url_path="bulk-approve")
    def bulk_approve(self, request):
        serializer = BulkReportApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report_ids = serializer.validated_data["report_ids"]

        reports = list(
            self.get_queryset().filter(id__in=report_ids)
        )

        found_ids = {report.id for report in reports}
        missing_ids = set(report_ids) - found_ids

        if missing_ids:
            raise ValidationError(
                {
                    "report_ids": (
                        f"Reports not found: {sorted(missing_ids)}"
                    )
                }
            )

        already_approved_ids = [
            report.id
            for report in reports
            if report.status == SessionReport.Status.APPROVED
        ]

        if already_approved_ids:
            raise ValidationError(
                {
                    "report_ids": (
                        f"Reports already approved: "
                        f"{already_approved_ids}"
                    )
                }
            )

        approved_ids = []
        approval_time = timezone.now()

        with transaction.atomic():
            for report in reports:
                old_status = report.status

                report.status = SessionReport.Status.APPROVED
                report.reviewed_by = request.user
                report.review_note = ""
                report.late_hours = report.calculate_late_hours(approval_time)
                report.save()

                ReportStatusHistory.objects.create(
                    session_report=report,
                    changed_by=request.user,
                    old_status=old_status,
                    new_status=SessionReport.Status.APPROVED,
                    note="",
                )

                approved_ids.append(report.id)

        return Response(
            {
                "approved_count": len(approved_ids),
                "approved_report_ids": approved_ids,
            }
        )