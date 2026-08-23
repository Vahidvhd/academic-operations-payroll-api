import calendar
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from core.models import SoftDeleteModel, TimeStampedModel


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


class TeacherClassAssignment(TimeStampedModel):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="class_assignments")
    course_class = models.ForeignKey(
        CourseClass,
        on_delete=models.PROTECT,
        related_name="teacher_assignments")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def clean(self):
        super().clean()

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

        if (
            self.course_class_id
            and self.start_date
            and self.start_date < self.course_class.start_date
        ):
            raise ValidationError({"start_date": "Assignment cannot start before the class starts."})

        if (
            self.course_class_id
            and self.end_date
            and self.end_date > self.course_class.end_date
        ):
            raise ValidationError({"end_date": "Assignment cannot end after the class ends."})
        
        if (
            self.course_class_id
            and self.start_date
            and self.start_date > self.course_class.end_date
        ):
            raise ValidationError({"start_date": "Assignment cannot start after the class ends."})

        if self.teacher_id and self.teacher.role != "teacher":
            raise ValidationError({"teacher": "Selected user must have the teacher role."})

        if self.course_class_id and self.start_date:
            new_end = self.end_date or self.course_class.end_date

            overlapping_assignments = TeacherClassAssignment.objects.filter(
                course_class=self.course_class,
                start_date__lte=new_end,
            ).exclude(
                end_date__lt=self.start_date,
            )
            if self.pk:
                overlapping_assignments = overlapping_assignments.exclude(pk=self.pk)
            if overlapping_assignments.exists():
                raise ValidationError({"start_date": "Assignment dates cannot overlap with another assignment for this class."})


class CourseSession(TimeStampedModel, SoftDeleteModel):
    course_class = models.ForeignKey(
        CourseClass,
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conducted_sessions",
        null=True,
        blank=True,
    )
    session_datetime = models.DateTimeField()
    session_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("course_class", "session_number"),
                condition=models.Q(is_deleted=False),
                name="unique_active_session_number_per_course_class",
            )
        ]

    def clean(self):
        if self.conducted_by_id and self.conducted_by.role != "teacher":
            raise ValidationError({"conducted_by": "Selected user must have the teacher role."})
        
        if not self.course_class_id or not self.session_datetime:
            return

        session_date = self.session_datetime.date()
        if session_date < self.course_class.start_date:
            raise ValidationError(
                {"session_datetime": "Session cannot be before the class starts."}
            )

        if session_date > self.course_class.end_date:
            raise ValidationError(
                {"session_datetime": "Session cannot be after the class ends."}
            )

        session_end = self.session_datetime + timedelta(
            minutes=self.course_class.session_duration
        )

        existing_sessions = CourseSession.objects.filter(
            course_class=self.course_class,
            is_deleted=False,
        )

        if self.pk:
            existing_sessions = existing_sessions.exclude(pk=self.pk)

        for existing_session in existing_sessions:
            existing_end = existing_session.session_datetime + timedelta(
                minutes=self.course_class.session_duration
            )

            if (self.session_datetime < existing_end and session_end > existing_session.session_datetime):
                raise ValidationError(
                    {"session_datetime": "Session cannot overlap with another session."}
                )

    def __str__(self):
        return f"{self.course_class} - Session {self.session_number}"
            