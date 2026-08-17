from rest_framework import serializers

from academics.models import TeacherClassAssignment
from reports.models import SessionReport


class SessionReportSerializer(serializers.ModelSerializer):
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

        return attrs