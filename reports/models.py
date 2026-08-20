import math
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


class SessionReport(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    session = models.OneToOneField("academics.CourseSession", on_delete=models.PROTECT, related_name="report")
    lesson_summary = models.TextField()
    present_count = models.PositiveIntegerField()
    absent_count = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField()
    late_hours = models.PositiveIntegerField(default=0)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_reports",
    )
    review_note = models.TextField(blank=True)

    def clean(self):
        super().clean()

        if self.session_id and self.submitted_at:
            session_end = self.session.session_datetime + timedelta(
                minutes=self.session.course_class.session_duration
            )

            if self.submitted_at < session_end:
                raise ValidationError({"session": ("Report can only be submitted after the session ends.")})

        if self.status == self.Status.REJECTED and not self.review_note.strip():
            raise ValidationError({"review_note": "A rejection reason is required."})

        if (self.status in [self.Status.APPROVED, self.Status.REJECTED] and not self.reviewed_by_id):
            raise ValidationError({"reviewed_by": "A reviewer is required for reviewed reports."})

        if (self.reviewed_by_id and self.reviewed_by.role != "education_officer"):
            raise ValidationError({"reviewed_by": "Reviewer must be an education officer."})

    def calculate_late_hours(self, approved_at):
        session_end = self.session.session_datetime + timedelta(
            minutes=self.session.course_class.session_duration
        )

        deadline = session_end + timedelta(hours=48)

        if approved_at <= deadline:
            return 0

        late_seconds = (approved_at - deadline).total_seconds()

        return math.ceil(late_seconds / 3600)


class ReportStatusHistory(TimeStampedModel):
    session_report = models.ForeignKey(
        SessionReport,
        on_delete=models.PROTECT,
        related_name="status_history",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="report_status_changes",
    )
    old_status = models.CharField(
        max_length=20,
        choices=SessionReport.Status.choices,
    )
    new_status = models.CharField(
        max_length=20,
        choices=SessionReport.Status.choices,
    )
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"Report {self.session_report_id}: "
            f"{self.old_status} -> {self.new_status}"
        )