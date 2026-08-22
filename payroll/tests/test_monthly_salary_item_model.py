from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from academics.models import CourseClass, CourseSession, School, Term
from payroll.models import MonthlySalary, MonthlySalaryItem
from reports.models import SessionReport

User = get_user_model()


class MonthlySalaryItemModelTests(TestCase):
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

        self.education_officer = User.objects.create_user(
            username="education",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.school = School.objects.create(
            name="Test School",
            address="London",
        )

        self.term = Term.objects.create(
            start_date=datetime(2026, 8, 1).date(),
            end_date=datetime(2026, 8, 31).date(),
            term_type=Term.TermType.REGULAR,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="PY-101",
            start_date=self.term.start_date,
            end_date=self.term.end_date,
            session_duration=CourseClass.SessionDuration.NINETY,
        )

        self.session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 10, 10, 0)
            ),
            session_number=1,
        )

        self.report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.APPROVED,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
            late_hours=10,
            reviewed_by=self.education_officer,
        )

        self.salary = MonthlySalary.objects.create(
            teacher=self.teacher,
            year=2026,
            month=8,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("200.00"),
            total_penalty_amount=Decimal("20.00"),
            net_amount=Decimal("180.00"),
        )

    def test_monthly_salary_item_can_be_created(self):
        item = MonthlySalaryItem.objects.create(
            monthly_salary=self.salary,
            session_report=self.report,
            amount_before_penalty=Decimal("200.00"),
            penalty_amount=Decimal("20.00"),
            amount_after_penalty=Decimal("180.00"),
        )

        self.assertEqual(item.monthly_salary, self.salary)
        self.assertEqual(item.session_report, self.report)
        self.assertEqual(item.amount_before_penalty, Decimal("200.00"))
        self.assertEqual(item.penalty_amount, Decimal("20.00"))
        self.assertEqual(item.amount_after_penalty, Decimal("180.00"))


    def test_penalty_amount_cannot_exceed_amount_before_penalty(self):
        item = MonthlySalaryItem(
            monthly_salary=self.salary,
            session_report=self.report,
            amount_before_penalty=Decimal("200.00"),
            penalty_amount=Decimal("250.00"),
            amount_after_penalty=Decimal("0.00"),
        )

        try:
            item.full_clean()
        except ValidationError as error:
            self.assertIn(
                "penalty_amount",
                error.message_dict,
            )
        else:
            self.fail("ValidationError was not raised.")


    def test_amount_after_penalty_must_equal_before_minus_penalty(self):
        item = MonthlySalaryItem(
            monthly_salary=self.salary,
            session_report=self.report,
            amount_before_penalty=Decimal("200.00"),
            penalty_amount=Decimal("20.00"),
            amount_after_penalty=Decimal("190.00"),
        )

        try:
            item.full_clean()
        except ValidationError as error:
            self.assertIn(
                "amount_after_penalty",
                error.message_dict,
            )
        else:
            self.fail("ValidationError was not raised.")


    def test_session_report_can_have_only_one_salary_item(self):
        MonthlySalaryItem.objects.create(
            monthly_salary=self.salary,
            session_report=self.report,
            amount_before_penalty=Decimal("200.00"),
            penalty_amount=Decimal("20.00"),
            amount_after_penalty=Decimal("180.00"),
        )

        duplicate_item = MonthlySalaryItem(
            monthly_salary=self.salary,
            session_report=self.report,
            amount_before_penalty=Decimal("200.00"),
            penalty_amount=Decimal("20.00"),
            amount_after_penalty=Decimal("180.00"),
        )

        try:
            duplicate_item.full_clean()
        except ValidationError as error:
            self.assertIn("session_report", error.message_dict)
        else:
            self.fail("ValidationError was not raised.")


    def test_penalty_amount_cannot_be_negative(self):
        item = MonthlySalaryItem(
            monthly_salary=self.salary,
            session_report=self.report,
            amount_before_penalty=Decimal("200.00"),
            penalty_amount=Decimal("-1.00"),
            amount_after_penalty=Decimal("201.00"),
        )

        try:
            item.full_clean()
        except ValidationError as error:
            self.assertIn(
                "penalty_amount",
                error.message_dict,
            )
        else:
            self.fail("ValidationError was not raised.")