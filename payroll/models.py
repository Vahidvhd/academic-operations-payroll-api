from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from academics.models import Term
from core.models import TimeStampedModel


class TeacherTermWage(TimeStampedModel):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="term_wages",
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.PROTECT,
        related_name="teacher_wages",
    )
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="wages_set",
    )
    base_wage_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("teacher", "term"),
                name="unique_teacher_wage_per_term",
            )
        ]

    def clean(self):
        super().clean()

        if self.teacher_id and self.teacher.role != self.teacher.Role.TEACHER:
            raise ValidationError({"teacher": "Selected user must have the teacher role."})

        if self.set_by_id and self.set_by.role != self.set_by.Role.FINANCE_OFFICER:
            raise ValidationError({"set_by": "Base wage must be set by a finance officer."})

    def __str__(self):
        return (f"{self.teacher} - {self.term} - {self.base_wage_rate}")