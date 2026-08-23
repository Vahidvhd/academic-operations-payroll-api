from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from academics.models import CourseClass, CourseSession, School, Term
from payroll.models import TeacherTermWage
from payroll.services import (
    apply_summer_multiplier,
    calculate_late_penalty,
    calculate_report_amount,
    calculate_session_amount,
    calculate_session_base_amount,
    get_approved_reports_for_teacher_month,
    get_teacher_sessions_for_month,
    get_teacher_term_wage,
)
from reports.models import SessionReport

User = get_user_model()


class CalculateSessionBaseAmountTests(SimpleTestCase):
    def test_ninety_minute_session_uses_full_base_wage(self):
        amount = calculate_session_base_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=90,
        )

        self.assertEqual(amount, Decimal("200.00"))

    def test_sixty_minute_session_uses_seventy_percent_of_base_wage(self):
        amount = calculate_session_base_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=60,
        )

        self.assertEqual(amount, Decimal("140.00"))

    def test_one_hundred_twenty_minute_session_uses_one_hundred_thirty_percent_of_base_wage(self):
        amount = calculate_session_base_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=120,
        )

        self.assertEqual(amount, Decimal("260.00"))

    def test_unsupported_session_duration_raises_value_error(self):
        try:
            calculate_session_base_amount(
                base_wage_rate=Decimal("200.00"),
                session_duration=75,
            )
        except ValueError as error:
            self.assertEqual(
                str(error),
                "Unsupported session duration.",
            )
        else:
            self.fail("ValueError was not raised.")


class ApplySummerMultiplierTests(SimpleTestCase):
    def test_summer_term_increases_amount_by_ten_percent(self):
        amount = apply_summer_multiplier(
            amount=Decimal("200.00"),
            is_summer=True,
        )

        self.assertEqual(amount, Decimal("220.00"))


    def test_non_summer_term_keeps_amount_unchanged(self):
        amount = apply_summer_multiplier(
            amount=Decimal("200.00"),
            is_summer=False,
        )

        self.assertEqual(amount, Decimal("200.00"))


class CalculateLatePenaltyTests(SimpleTestCase):
    def test_late_hours_apply_one_percent_penalty_per_hour(self):
        penalty = calculate_late_penalty(amount=Decimal("200.00"), late_hours=10)

        self.assertEqual(penalty, Decimal("20.00"))


    def test_zero_late_hours_has_no_penalty(self):
        penalty = calculate_late_penalty(amount=Decimal("200.00"), late_hours=0)

        self.assertEqual(penalty, Decimal("0.00"))


    def test_late_penalty_is_capped_at_one_hundred_percent(self):
        penalty = calculate_late_penalty(amount=Decimal("200.00"), late_hours=150)

        self.assertEqual(penalty, Decimal("200.00"))


class CalculateSessionAmountTests(SimpleTestCase):
    def test_calculates_final_session_amount(self):
        (
            amount_before_penalty,
            penalty_amount,
            amount_after_penalty,
        ) = calculate_session_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=90,
            is_summer=True,
            late_hours=10,
        )

        self.assertEqual(
            amount_before_penalty,
            Decimal("220.00"),
        )
        self.assertEqual(
            penalty_amount,
            Decimal("22.00"),
        )
        self.assertEqual(
            amount_after_penalty,
            Decimal("198.00"),
        )


    def test_rounds_session_amounts_to_two_decimal_places(self):
        (amount_before_penalty, penalty_amount, amount_after_penalty) = calculate_session_amount(
            base_wage_rate=Decimal("199.99"),
            session_duration=120,
            is_summer=True,
            late_hours=1,
        )

        self.assertEqual(amount_before_penalty, Decimal("285.99"))
        self.assertEqual(penalty_amount, Decimal("2.86"))
        self.assertEqual(amount_after_penalty, Decimal("283.13"))


    def test_one_hundred_percent_penalty_makes_final_amount_zero(self):
        (amount_before_penalty, penalty_amount, amount_after_penalty) = calculate_session_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=90,
            is_summer=False,
            late_hours=150,
        )

        self.assertEqual(amount_before_penalty, Decimal("200.00"))
        self.assertEqual(penalty_amount, Decimal("200.00"))
        self.assertEqual(amount_after_penalty, Decimal("0.00"))


class GetTeacherSessionsForMonthTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher",
            role=User.Role.TEACHER,
        )

        self.school = School.objects.create(
            name="Test School",
            address="London",
        )

        self.term = Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-10-31",
            term_type=Term.TermType.REGULAR,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="PY101",
            start_date="2026-09-01",
            end_date="2026-10-31",
            session_duration=90,
        )

    def test_returns_only_teacher_sessions_from_requested_month(self):
        september_session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-10-10T10:00:00Z",
            session_number=2,
        )

        sessions = get_teacher_sessions_for_month(
            self.teacher,
            2026,
            9,
        )

        self.assertEqual(sessions.count(), 1)
        self.assertEqual(sessions.first(), september_session)


    def test_salary_reports_fail_when_session_has_no_report(self):
        CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        try:
            get_approved_reports_for_teacher_month(
                self.teacher,
                2026,
                9,
            )
        except ValueError as error:
            self.assertEqual(
                str(error),
                "All sessions must have a report before salary calculation.",
            )
        else:
            self.fail("ValueError was not raised.")


    def test_salary_reports_fail_when_report_is_pending(self):
        session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        SessionReport.objects.create(
            session=session,
            lesson_summary="Test lesson",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-10T12:00:00Z",
        )

        try:
            get_approved_reports_for_teacher_month(
                self.teacher,
                2026,
                9,
            )
        except ValueError as error:
            self.assertEqual(
                str(error),
                "All reports must be approved before salary calculation.",
            )
        else:
            self.fail("ValueError was not raised.")


    def test_returns_approved_reports_for_teacher_month(self):
        session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        report = SessionReport.objects.create(
            session=session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Test lesson",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-10T12:00:00Z",
        )

        reports = get_approved_reports_for_teacher_month(
            self.teacher,
            2026,
            9,
        )

        self.assertEqual(reports.count(), 1)
        self.assertEqual(reports.first(), report)


class GetTeacherTermWageTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="wage_teacher",
            role=User.Role.TEACHER,
        )

        self.finance_officer = User.objects.create_user(
            username="finance_officer",
            role=User.Role.FINANCE_OFFICER,
        )

        self.term = Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-09-30",
            term_type=Term.TermType.REGULAR,
        )


    def test_returns_teacher_wage_for_term(self):
        wage = TeacherTermWage.objects.create(
            teacher=self.teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        result = get_teacher_term_wage(
            self.teacher,
            self.term,
        )

        self.assertEqual(result, wage)


    def test_raises_error_when_teacher_wage_is_missing(self):
        try:
            get_teacher_term_wage(
                self.teacher,
                self.term,
            )
        except ValueError as error:
            self.assertEqual(
                str(error),
                (
                    f"Base wage is not set for teacher "
                    f"{self.teacher.id} and term {self.term.id}."
                ),
            )
        else:
            self.fail("ValueError was not raised.")


class CalculateReportAmountTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="report_amount_teacher",
            role=User.Role.TEACHER,
        )

        self.finance_officer = User.objects.create_user(
            username="report_amount_finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.school = School.objects.create(
            name="Report Amount School",
            address="London",
        )

        self.term = Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-09-30",
            term_type=Term.TermType.REGULAR,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="RA101",
            start_date="2026-09-01",
            end_date="2026-09-30",
            session_duration=90,
        )

        TeacherTermWage.objects.create(
            teacher=self.teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )


    def test_calculates_amount_for_approved_report(self):
        session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        report = SessionReport.objects.create(
            session=session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Test lesson",
            present_count=10,
            absent_count=0,
            late_hours=10,
            submitted_at="2026-09-10T12:00:00Z",
        )

        (
            amount_before_penalty,
            penalty_amount,
            amount_after_penalty,
        ) = calculate_report_amount(
            report,
            self.teacher,
        )

        self.assertEqual(
            amount_before_penalty,
            Decimal("200.00"),
        )
        self.assertEqual(
            penalty_amount,
            Decimal("20.00"),
        )
        self.assertEqual(
            amount_after_penalty,
            Decimal("180.00"),
        )


    def test_applies_summer_multiplier_to_report_amount(self):
        self.term.term_type = Term.TermType.SUMMER
        self.term.save()

        session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        report = SessionReport.objects.create(
            session=session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Test lesson",
            present_count=10,
            absent_count=0,
            late_hours=0,
            submitted_at="2026-09-10T12:00:00Z",
        )

        (
            amount_before_penalty,
            penalty_amount,
            amount_after_penalty,
        ) = calculate_report_amount(
            report,
            self.teacher,
        )

        self.assertEqual(
            amount_before_penalty,
            Decimal("220.00"),
        )
        self.assertEqual(
            penalty_amount,
            Decimal("0.00"),
        )
        self.assertEqual(
            amount_after_penalty,
            Decimal("220.00"),
        )