from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from academics.models import Term
from core.models import TimeStampedModel
from reports.models import SessionReport


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


class MonthlySalary(TimeStampedModel):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="monthly_salaries",
    )
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12),
        ]
    )
    calculated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="calculated_salaries",
    )
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_penalty_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("teacher", "year", "month"),
                name="unique_teacher_monthly_salary",
            )
        ]

    def clean(self):
        super().clean()

        if self.teacher_id and self.teacher.role != self.teacher.Role.TEACHER:
            raise ValidationError(
                {"teacher": "Selected user must have the teacher role."}
            )

        if (
            self.calculated_by_id
            and self.calculated_by.role
            != self.calculated_by.Role.FINANCE_OFFICER
        ):
            raise ValidationError(
                {"calculated_by": ("Salary must be calculated by a finance officer.")})

        if (
            self.gross_amount is not None
            and self.total_penalty_amount is not None
            and self.total_penalty_amount > self.gross_amount
        ):
            raise ValidationError({"total_penalty_amount": ("Total penalty cannot exceed gross amount.")})

        if (
            self.gross_amount is not None
            and self.total_penalty_amount is not None
            and self.net_amount is not None
            and self.net_amount
            != self.gross_amount - self.total_penalty_amount
        ):
            raise ValidationError({"net_amount": ("Net amount must equal gross amount minus total penalty.")})

    def __str__(self):
        return (
            f"{self.teacher} - "
            f"{self.year}-{self.month:02d} - "
            f"{self.net_amount}"
        )


class MonthlySalaryItem(TimeStampedModel):
    monthly_salary = models.ForeignKey(
        MonthlySalary,
        on_delete=models.CASCADE,
        related_name="items",
    )
    session_report = models.OneToOneField(
        SessionReport,
        on_delete=models.PROTECT,
        related_name="salary_item",
    )
    amount_before_penalty = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    penalty_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    amount_after_penalty = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    def clean(self):
        super().clean()

        if self.penalty_amount > self.amount_before_penalty:
            raise ValidationError({"penalty_amount": ("Penalty amount cannot exceed amount before penalty.")})

        if (self.amount_after_penalty != self.amount_before_penalty - self.penalty_amount):
            raise ValidationError(
                {
                    "amount_after_penalty": (
                        "Amount after penalty must equal amount before "
                        "penalty minus penalty amount."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.monthly_salary} - "
            f"Report {self.session_report_id} - "
            f"{self.amount_after_penalty}"
        )