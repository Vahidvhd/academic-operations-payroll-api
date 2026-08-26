from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from payroll.models import MonthlySalary

User = get_user_model()


class MonthlySalaryModelTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher",
            role=User.Role.TEACHER,
            phone_number="07111111111",
            emergency_phone_number="07222222222",
        )

        self.finance_officer = User.objects.create_user(
            username="finance",
            role=User.Role.FINANCE_OFFICER,
        )


    def test_monthly_salary_can_be_created(self):
        salary = MonthlySalary.objects.create(
            teacher=self.teacher,
            year=2026,
            month=8,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("500.00"),
            total_penalty_amount=Decimal("50.00"),
            net_amount=Decimal("450.00"),
        )

        self.assertEqual(salary.teacher, self.teacher)
        self.assertEqual(salary.year, 2026)
        self.assertEqual(salary.month, 8)
        self.assertEqual(
            salary.calculated_by,
            self.finance_officer,
        )
        self.assertEqual(
            salary.gross_amount,
            Decimal("500.00"),
        )
        self.assertEqual(
            salary.total_penalty_amount,
            Decimal("50.00"),
        )
        self.assertEqual(
            salary.net_amount,
            Decimal("450.00"),
        )


    def test_teacher_must_have_teacher_role(self):
        salary = MonthlySalary(
            teacher=self.finance_officer,
            year=2026,
            month=8,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("500.00"),
            total_penalty_amount=Decimal("50.00"),
            net_amount=Decimal("450.00"),
        )

        with self.assertRaises(ValidationError) as context:
            salary.full_clean()

        self.assertIn("teacher", context.exception.message_dict)


    def test_calculated_by_must_have_finance_officer_role(self):
        salary = MonthlySalary(
            teacher=self.teacher,
            year=2026,
            month=8,
            calculated_by=self.teacher,
            gross_amount=Decimal("500.00"),
            total_penalty_amount=Decimal("50.00"),
            net_amount=Decimal("450.00"),
        )

        with self.assertRaises(ValidationError) as context:
            salary.full_clean()

        self.assertIn("calculated_by", context.exception.message_dict)


    def test_month_must_be_between_one_and_twelve(self):
        salary = MonthlySalary(
            teacher=self.teacher,
            year=2026,
            month=13,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("500.00"),
            total_penalty_amount=Decimal("50.00"),
            net_amount=Decimal("450.00"),
        )

        try:
            salary.full_clean()
        except ValidationError as error:
            self.assertIn("month", error.message_dict)
        else:
            self.fail("ValidationError was not raised.")


    def test_teacher_year_and_month_must_be_unique(self):
        MonthlySalary.objects.create(
            teacher=self.teacher,
            year=2026,
            month=8,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("500.00"),
            total_penalty_amount=Decimal("50.00"),
            net_amount=Decimal("450.00"),
        )

        duplicate_salary = MonthlySalary(
            teacher=self.teacher,
            year=2026,
            month=8,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("600.00"),
            total_penalty_amount=Decimal("60.00"),
            net_amount=Decimal("540.00"),
        )

        try:
            duplicate_salary.full_clean()
        except ValidationError as error:
            self.assertIn("__all__", error.message_dict)
        else:
            self.fail("ValidationError was not raised.")


    def test_total_penalty_cannot_exceed_gross_amount(self):
        salary = MonthlySalary(
            teacher=self.teacher,
            year=2026,
            month=8,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("500.00"),
            total_penalty_amount=Decimal("600.00"),
            net_amount=Decimal("0.00"),
        )

        try:
            salary.full_clean()
        except ValidationError as error:
            self.assertIn(
                "total_penalty_amount",
                error.message_dict,
            )
        else:
            self.fail("ValidationError was not raised.")


    def test_net_amount_must_equal_gross_minus_penalty(self):
        salary = MonthlySalary(
            teacher=self.teacher,
            year=2026,
            month=8,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("500.00"),
            total_penalty_amount=Decimal("50.00"),
            net_amount=Decimal("460.00"),
        )

        try:
            salary.full_clean()
        except ValidationError as error:
            self.assertIn(
                "net_amount",
                error.message_dict,
            )
        else:
            self.fail("ValidationError was not raised.")