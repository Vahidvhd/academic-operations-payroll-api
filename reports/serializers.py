from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from academics.models import CourseSession, TeacherClassAssignment
from reports.models import SessionReport


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
            session_date = session.session_datetime.date()

            owns_session = TeacherClassAssignment.objects.filter(
                teacher=request.user,
                course_class=session.course_class,
                start_date__lte=session_date,
            ).exclude(end_date__lt=session_date).exists()

            if not owns_session:
                raise serializers.ValidationError({"session": ("You can only report sessions from your own assignment.")})

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
        validated_data["status"] = SessionReport.Status.PENDING
        validated_data["submitted_at"] = timezone.now()

        return super().update(instance, validated_data)


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