import calendar

from django.core.exceptions import ValidationError
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class School(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    address = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("name", "address"),
                name="unique_school_name_address",
            )
        ]

    def __str__(self):
        return self.name

class Term(TimeStampedModel, SoftDeleteModel):
    class TermType(models.TextChoices):
        REGULAR = "regular", "Regular"
        SUMMER = "summer", "Summer"

    start_date = models.DateField()
    end_date = models.DateField()
    term_type = models.CharField(max_length=10, choices=TermType.choices)

    def clean(self):
        super().clean()

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

        if self.start_date and self.start_date.day != 1:
            raise ValidationError({"start_date": "Start date must be the first day of a month."})

        if self.end_date:
            last_day = calendar.monthrange(self.end_date.year, self.end_date.month)[1]
            if self.end_date.day != last_day:
                raise ValidationError({"end_date": "End date must be the last day of a month."})

        if self.start_date and self.end_date:
            overlapping_terms = Term.objects.filter(is_deleted=False,
                                                    start_date__lte=self.end_date,
                                                    end_date__gte=self.start_date)

            if self.pk:
                overlapping_terms = overlapping_terms.exclude(pk=self.pk)

            if overlapping_terms.exists():
                raise ValidationError({"start_date": "Term dates cannot overlap with another term."})
  
    def __str__(self):
        return (
            f"{self.get_term_type_display()} "
            f"({self.start_date} - {self.end_date})"
        )


class CourseClass(TimeStampedModel, SoftDeleteModel):
    class SessionDuration(models.IntegerChoices):
        SIXTY = 60, "60 minutes"
        NINETY = 90, "90 minutes"
        ONE_HUNDRED_TWENTY = 120, "120 minutes"
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="course_classes")
    term = models.ForeignKey(Term, on_delete=models.PROTECT, related_name="course_classes")
    title = models.CharField(max_length=255)
    class_code = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    session_duration = models.PositiveSmallIntegerField(choices=SessionDuration.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("school", "term", "class_code"),
                name="unique_course_class_code_per_school_term",
            )
        ]

    def clean(self):
        super().clean()

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

        if (self.term_id and self.start_date and self.start_date < self.term.start_date):
            raise ValidationError({"start_date": "Class cannot start before the term starts."})

        if ( self.term_id and self.end_date and self.end_date > self.term.end_date):
            raise ValidationError({"end_date": "Class cannot end after the term ends."})

    def __str__(self):
        return f"{self.title} ({self.class_code})"