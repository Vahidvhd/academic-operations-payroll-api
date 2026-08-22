from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from academics.models import Term
from payroll.models import TeacherTermWage

User = get_user_model()


class TeacherTermWageModelTests(TestCase):
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

        self.term = Term.objects.create(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            term_type=Term.TermType.REGULAR,
        )

    def test_teacher_term_wage_can_be_created(self):
        wage = TeacherTermWage.objects.create(
            teacher=self.teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        self.assertEqual(wage.teacher, self.teacher)
        self.assertEqual(wage.term, self.term)
        self.assertEqual(wage.set_by, self.finance_officer)
        self.assertEqual(
            wage.base_wage_rate,
            Decimal("200.00"),
        )


    def test_teacher_must_have_teacher_role(self):
        wage = TeacherTermWage(
            teacher=self.finance_officer,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        with self.assertRaises(ValidationError):
            wage.full_clean()