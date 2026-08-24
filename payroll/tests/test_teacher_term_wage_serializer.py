from datetime import date

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from academics.models import Term
from payroll.serializers import (
    PayrollCalculationSerializer,
    TeacherTermWageSerializer,
)

User = get_user_model()


class TeacherTermWageSerializerTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher",
            role=User.Role.TEACHER,
            phone_number="07111111111",
            emergency_phone_number="07222222222",
        )

        self.term = Term.objects.create(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            term_type=Term.TermType.REGULAR,
        )

        self.finance_officer = User.objects.create_user(
            username="finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.deleted_term = Term.objects.create(
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            term_type=Term.TermType.REGULAR,
            is_deleted=True,
        )

    def test_valid_data_is_accepted(self):
        serializer = TeacherTermWageSerializer(
            data={
                "teacher": self.teacher.id,
                "term": self.term.id,
                "base_wage_rate": "200.00",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)


    def test_finance_officer_cannot_be_used_as_teacher(self):
        serializer = TeacherTermWageSerializer(
            data={
                "teacher": self.finance_officer.id,
                "term": self.term.id,
                "base_wage_rate": "200.00",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("teacher", serializer.errors)


    def test_deleted_term_is_rejected(self):
        serializer = TeacherTermWageSerializer(
            data={
                "teacher": self.teacher.id,
                "term": self.deleted_term.id,
                "base_wage_rate": "200.00",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("term", serializer.errors)


    def test_zero_base_wage_rate_is_rejected(self):
        serializer = TeacherTermWageSerializer(
            data={
                "teacher": self.teacher.id,
                "term": self.term.id,
                "base_wage_rate": "0.00",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("base_wage_rate", serializer.errors)


    def test_set_by_is_read_only(self):
        serializer = TeacherTermWageSerializer(
            data={
                "teacher": self.teacher.id,
                "term": self.term.id,
                "base_wage_rate": "200.00",
                "set_by": self.finance_officer.id,
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )
        self.assertNotIn(
            "set_by",
            serializer.validated_data,
        )


class PayrollCalculationSerializerTests(SimpleTestCase):
    def test_valid_year_and_month(self):
        serializer = PayrollCalculationSerializer(
            data={
                "year": 2026,
                "month": 9,
            }
        )

        self.assertTrue(serializer.is_valid())

    def test_invalid_month(self):
        serializer = PayrollCalculationSerializer(
            data={
                "year": 2026,
                "month": 13,
            }
        )

        self.assertFalse(serializer.is_valid())