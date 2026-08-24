from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from academics.models import CourseClass, CourseSession, School, Term
from payroll.models import MonthlySalary, MonthlySalaryItem, TeacherTermWage
from payroll.services import (
    apply_summer_multiplier,
    calculate_all_teacher_salaries_for_month,
    calculate_late_penalty,
    calculate_report_amount,
    calculate_session_amount,
    calculate_session_base_amount,
    calculate_teacher_month_totals,
    calculate_teacher_monthly_salary,
    get_approved_reports_for_teacher_month,
    get_teacher_sessions_for_month,
    get_teacher_term_wage,
    get_teachers_for_month,
    validate_month_ready_for_payroll,
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


class CalculateTeacherMonthTotalsTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="monthly_total_teacher",
            role=User.Role.TEACHER,
        )

        self.finance_officer = User.objects.create_user(
            username="monthly_total_finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.school = School.objects.create(
            name="Monthly Total School",
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
            class_code="MT101",
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


    def test_calculates_month_totals_from_multiple_reports(self):
        session1 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        session2 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=2,
        )

        SessionReport.objects.create(
            session=session1,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 1",
            present_count=10,
            absent_count=0,
            late_hours=10,
            submitted_at="2026-09-10T12:00:00Z",
        )

        SessionReport.objects.create(
            session=session2,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 2",
            present_count=10,
            absent_count=0,
            late_hours=0,
            submitted_at="2026-09-20T12:00:00Z",
        )

        gross_amount, total_penalty_amount, net_amount = (
            calculate_teacher_month_totals(
                self.teacher,
                2026,
                9,
            )
        )

        self.assertEqual(gross_amount, Decimal("400.00"))
        self.assertEqual(total_penalty_amount, Decimal("20.00"))
        self.assertEqual(net_amount, Decimal("380.00"))


    def test_creates_monthly_salary_with_correct_totals(self):
        session1 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        session2 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=2,
        )

        SessionReport.objects.create(
            session=session1,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 1",
            present_count=10,
            absent_count=0,
            late_hours=10,
            submitted_at="2026-09-10T12:00:00Z",
        )

        SessionReport.objects.create(
            session=session2,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 2",
            present_count=10,
            absent_count=0,
            late_hours=0,
            submitted_at="2026-09-20T12:00:00Z",
        )

        salary = calculate_teacher_monthly_salary(
            self.teacher,
            2026,
            9,
            self.finance_officer,
        )

        self.assertEqual(MonthlySalary.objects.count(), 1)
        self.assertEqual(salary.teacher, self.teacher)
        self.assertEqual(salary.year, 2026)
        self.assertEqual(salary.month, 9)
        self.assertEqual(
            salary.calculated_by,
            self.finance_officer,
        )
        self.assertEqual(
            salary.gross_amount,
            Decimal("400.00"),
        )
        self.assertEqual(
            salary.total_penalty_amount,
            Decimal("20.00"),
        )
        self.assertEqual(
            salary.net_amount,
            Decimal("380.00"),
        )


    def test_recalculates_existing_monthly_salary(self):
        existing_salary = MonthlySalary.objects.create(
            teacher=self.teacher,
            year=2026,
            month=9,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("100.00"),
            total_penalty_amount=Decimal("0.00"),
            net_amount=Decimal("100.00"),
        )

        session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        SessionReport.objects.create(
            session=session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson",
            present_count=10,
            absent_count=0,
            late_hours=10,
            submitted_at="2026-09-10T12:00:00Z",
        )

        salary = calculate_teacher_monthly_salary(
            self.teacher,
            2026,
            9,
            self.finance_officer,
        )

        self.assertEqual(MonthlySalary.objects.count(), 1)
        self.assertEqual(salary.id, existing_salary.id)
        self.assertEqual(
            salary.gross_amount,
            Decimal("200.00"),
        )
        self.assertEqual(
            salary.total_penalty_amount,
            Decimal("20.00"),
        )
        self.assertEqual(
            salary.net_amount,
            Decimal("180.00"),
        )


    def test_creates_salary_item_for_report(self):
        session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        report = SessionReport.objects.create(
            session=session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson",
            present_count=10,
            absent_count=0,
            late_hours=10,
            submitted_at="2026-09-10T12:00:00Z",
        )

        salary = calculate_teacher_monthly_salary(
            self.teacher,
            2026,
            9,
            self.finance_officer,
        )

        item = MonthlySalaryItem.objects.get(
            monthly_salary=salary,
            session_report=report,
        )

        self.assertEqual(
            item.amount_before_penalty,
            Decimal("200.00"),
        )
        self.assertEqual(
            item.penalty_amount,
            Decimal("20.00"),
        )
        self.assertEqual(
            item.amount_after_penalty,
            Decimal("180.00"),
        )


    def test_creates_salary_item_for_each_report(self):
        session1 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        session2 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=2,
        )

        SessionReport.objects.create(
            session=session1,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 1",
            present_count=10,
            absent_count=0,
            late_hours=10,
            submitted_at="2026-09-10T12:00:00Z",
        )

        SessionReport.objects.create(
            session=session2,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 2",
            present_count=10,
            absent_count=0,
            late_hours=0,
            submitted_at="2026-09-20T12:00:00Z",
        )

        salary = calculate_teacher_monthly_salary(
            self.teacher,
            2026,
            9,
            self.finance_officer,
        )

        self.assertEqual(
            MonthlySalaryItem.objects.filter(
                monthly_salary=salary,
            ).count(),
            2,
        )


    def test_recalculation_does_not_duplicate_salary_items(self):
        session1 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        session2 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=2,
        )

        SessionReport.objects.create(
            session=session1,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 1",
            present_count=10,
            absent_count=0,
            late_hours=10,
            submitted_at="2026-09-10T12:00:00Z",
        )

        SessionReport.objects.create(
            session=session2,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 2",
            present_count=10,
            absent_count=0,
            late_hours=0,
            submitted_at="2026-09-20T12:00:00Z",
        )

        first_salary = calculate_teacher_monthly_salary(
            self.teacher,
            2026,
            9,
            self.finance_officer,
        )

        second_salary = calculate_teacher_monthly_salary(
            self.teacher,
            2026,
            9,
            self.finance_officer,
        )

        self.assertEqual(MonthlySalary.objects.count(), 1)
        self.assertEqual(first_salary.id, second_salary.id)

        self.assertEqual(
            MonthlySalaryItem.objects.filter(
                monthly_salary=second_salary,
            ).count(),
            2,
        )


class ValidateMonthReadyForPayrollTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="validation_teacher",
            role=User.Role.TEACHER,
        )

        self.school = School.objects.create(
            name="Validation School",
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
            class_code="VAL101",
            start_date="2026-09-01",
            end_date="2026-09-30",
            session_duration=90,
        )

    def test_month_is_not_ready_when_any_report_is_pending(self):
        approved_session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        SessionReport.objects.create(
            session=approved_session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Approved lesson",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-10T12:00:00Z",
        )

        second_teacher = User.objects.create_user(
            username="second_teacher",
            role=User.Role.TEACHER,
        )

        pending_session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=second_teacher,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=2,
        )

        SessionReport.objects.create(
            session=pending_session,
            status=SessionReport.Status.PENDING,
            lesson_summary="Pending lesson",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-20T12:00:00Z",
        )

        try:
            validate_month_ready_for_payroll(2026, 9)
        except ValueError as error:
            self.assertEqual(
                str(error),
                "All reports must be approved before payroll calculation.",
            )
        else:
            self.fail("ValueError was not raised.")


    def test_month_is_not_ready_when_session_has_no_report(self):
        CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        try:
            validate_month_ready_for_payroll(2026, 9)
        except ValueError as error:
            self.assertEqual(
                str(error),
                "All sessions must have a report before payroll calculation.",
            )
        else:
            self.fail("ValueError was not raised.")


    def test_month_is_ready_when_all_reports_are_approved(self):
        session1 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        session2 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=2,
        )

        report1 = SessionReport.objects.create(
            session=session1,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 1",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-10T12:00:00Z",
        )

        report2 = SessionReport.objects.create(
            session=session2,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 2",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-20T12:00:00Z",
        )

        reports = validate_month_ready_for_payroll(2026, 9)

        self.assertEqual(reports.count(), 2)
        self.assertIn(report1, reports)
        self.assertIn(report2, reports)


class GetTeachersForMonthTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="month_teacher",
            role=User.Role.TEACHER,
        )

        self.second_teacher = User.objects.create_user(
            username="second_month_teacher",
            role=User.Role.TEACHER,
        )

        self.school = School.objects.create(
            name="Teacher Month School",
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
            class_code="TM101",
            start_date="2026-09-01",
            end_date="2026-09-30",
            session_duration=90,
        )

    def test_returns_each_teacher_only_once(self):
        CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime="2026-09-15T10:00:00Z",
            session_number=2,
        )

        CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.second_teacher,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=3,
        )

        teachers = get_teachers_for_month(2026, 9)

        self.assertEqual(teachers.count(), 2)
        self.assertIn(self.teacher, teachers)
        self.assertIn(self.second_teacher, teachers)


    def test_returns_substitute_teacher_for_conducted_session(self):
        CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.second_teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        teachers = get_teachers_for_month(2026, 9)

        self.assertEqual(teachers.count(), 1)
        self.assertIn(self.second_teacher, teachers)


class CalculateAllTeacherSalariesForMonthTests(TestCase):
    def setUp(self):
        self.teacher1 = User.objects.create_user(
            username="bulk_teacher_1",
            role=User.Role.TEACHER,
        )

        self.teacher2 = User.objects.create_user(
            username="bulk_teacher_2",
            role=User.Role.TEACHER,
        )

        self.finance_officer = User.objects.create_user(
            username="bulk_finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.school = School.objects.create(
            name="Bulk School",
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
            class_code="BULK101",
            start_date="2026-09-01",
            end_date="2026-09-30",
            session_duration=90,
        )

        TeacherTermWage.objects.create(
            teacher=self.teacher1,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        TeacherTermWage.objects.create(
            teacher=self.teacher2,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )


    def test_calculates_salary_for_all_teachers_in_month(self):
        session1 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher1,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        session2 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher2,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=2,
        )

        SessionReport.objects.create(
            session=session1,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 1",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-10T12:00:00Z",
        )

        SessionReport.objects.create(
            session=session2,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 2",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-20T12:00:00Z",
        )

        salaries = calculate_all_teacher_salaries_for_month(
            2026,
            9,
            self.finance_officer,
        )

        self.assertEqual(len(salaries), 2)
        self.assertEqual(MonthlySalary.objects.count(), 2)

        salary_teachers = {salary.teacher for salary in salaries}

        self.assertEqual(
            salary_teachers,
            {self.teacher1, self.teacher2},
        )


    def test_does_not_calculate_any_salary_when_month_is_not_ready(self):
        session1 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher1,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        session2 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher2,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=2,
        )

        SessionReport.objects.create(
            session=session1,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 1",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-10T12:00:00Z",
        )

        SessionReport.objects.create(
            session=session2,
            status=SessionReport.Status.PENDING,
            lesson_summary="Lesson 2",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-20T12:00:00Z",
        )

        try:
            calculate_all_teacher_salaries_for_month(
                2026,
                9,
                self.finance_officer,
            )
        except ValueError as error:
            self.assertEqual(
                str(error),
                "All reports must be approved before payroll calculation.",
            )
        else:
            self.fail("ValueError was not raised.")

        self.assertEqual(MonthlySalary.objects.count(), 0)


    def test_bulk_fails_when_teacher_wage_is_missing(self):
        TeacherTermWage.objects.filter(
            teacher=self.teacher2,
            term=self.term,
        ).delete()

        session1 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher1,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        session2 = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher2,
            session_datetime="2026-09-20T10:00:00Z",
            session_number=2,
        )

        SessionReport.objects.create(
            session=session1,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 1",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-10T12:00:00Z",
        )

        SessionReport.objects.create(
            session=session2,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Lesson 2",
            present_count=10,
            absent_count=0,
            submitted_at="2026-09-20T12:00:00Z",
        )

        try:
            calculate_all_teacher_salaries_for_month(
                2026,
                9,
                self.finance_officer,
            )
        except ValueError as error:
            self.assertEqual(
                str(error),
                f"Base wage is not set for teacher {self.teacher2.id} and term {self.term.id}.",
            )
        else:
            self.fail("ValueError was not raised.")

        self.assertEqual(MonthlySalary.objects.count(), 0)