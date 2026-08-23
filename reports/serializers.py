from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from academics.models import CourseSession
from reports.models import ReportStatusHistory, SessionReport


class SessionReportSerializer(serializers.ModelSerializer):
    session = serializers.PrimaryKeyRelatedField(
        queryset=CourseSession.objects.filter(is_deleted=False)
    )
    
    class Meta:
        model = SessionReport
        fields = [
            "id",
            "session",
            "lesson_summary",
            "present_count",
            "absent_count",
            "status",
            "submitted_at",
            "late_hours",
            "reviewed_by",
            "review_note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "submitted_at",
            "late_hours",
            "reviewed_by",
            "review_note",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        request = self.context.get("request")

        if (
            self.instance is None
            and request
            and request.user.role == "teacher"
        ):
            session = attrs.get("session")
            owns_session = session.get_effective_teacher() == request.user

            if not owns_session:
                raise serializers.ValidationError({"session": ("You can only report sessions assigned to or conducted by you.")})

        if (
            self.instance is not None
            and "session" in attrs
            and attrs["session"] != self.instance.session
        ):
            raise serializers.ValidationError(
                {"session": "Session cannot be changed after report creation."}
            )

        return attrs

    def create(self, validated_data):
        report = SessionReport(
            **validated_data,
            submitted_at=timezone.now(),
        )

        try:
            report.full_clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        report.save()
        return report

    def update(self, instance, validated_data):
        request = self.context["request"]
        old_status = instance.status

        validated_data["status"] = SessionReport.Status.PENDING
        validated_data["submitted_at"] = timezone.now()

        with transaction.atomic():
            report = super().update(instance, validated_data)

            ReportStatusHistory.objects.create(
                session_report=report,
                changed_by=request.user,
                old_status=old_status,
                new_status=report.status,
            )

        return report
    

class SessionReportReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionReport
        fields = [
            "status",
            "review_note",
        ]

    def validate(self, attrs):
        status = attrs.get("status")
        review_note = attrs.get("review_note", "").strip()

        if status not in [
            SessionReport.Status.APPROVED,
            SessionReport.Status.REJECTED,
        ]:
            raise serializers.ValidationError(
                {"status": "Status must be approved or rejected."}
            )

        if status == SessionReport.Status.REJECTED and not review_note:
            raise serializers.ValidationError(
                {"review_note": "Review note is required when rejecting a report."}
            )

        return attrs


class ReportStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStatusHistory
        fields = [
            "id",
            "old_status",
            "new_status",
            "changed_by",
            "note",
            "created_at",
        ]

        read_only_fields = fields


class MonthlyReportSummaryQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(
        min_value=2000,
    )
    month = serializers.IntegerField(
        min_value=1,
        max_value=12,
    )


class BulkReportApprovalSerializer(serializers.Serializer):
    report_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )

    def validate_report_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Duplicate report IDs are not allowed."
            )

        return value