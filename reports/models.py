from django.conf import settings
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