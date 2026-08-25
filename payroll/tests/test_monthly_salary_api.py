from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from academics.models import CourseClass, CourseSession, School, Term
from payroll.models import MonthlySalary, TeacherTermWage
from reports.models import SessionReport

User = get_user_model()


class MonthlySalaryAPITests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="salary_teacher",
            role=User.Role.TEACHER,
        )

        self.finance_officer = User.objects.create_user(
            username="salary_finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.school = School.objects.create(
            name="Salary School",
            address="London",
        )

        self.term = Term.objects.create(
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            term_type=Term.TermType.REGULAR,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="SAL101",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            session_duration=90,
        )

        TeacherTermWage.objects.create(
            teacher=self.teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        self.url = reverse("monthly-salary-calculate")

    def test_finance_officer_can_calculate_monthly_salaries(self):
        session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 10, 10, 0)
            ),
            session_number=1,
        )

        SessionReport.objects.create(
            session=session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Python lesson",
            present_count=10,
            absent_count=0,
            submitted_at=timezone.make_aware(
                datetime(2026, 9, 10, 12, 0)
            ),
        )

        self.client.force_authenticate(
            user=self.finance_officer
        )

        response = self.client.post(
            self.url,
            {
                "year": 2026,
                "month": 9,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MonthlySalary.objects.count(), 1)

        salary = MonthlySalary.objects.get()

        self.assertEqual(salary.teacher, self.teacher)
        self.assertEqual(salary.gross_amount, Decimal("200.00"))
        self.assertEqual(salary.net_amount, Decimal("200.00"))


    def test_teacher_cannot_calculate_monthly_salaries(self):
        self.client.force_authenticate(
            user=self.teacher
        )

        response = self.client.post(
            self.url,
            {
                "year": 2026,
                "month": 9,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(MonthlySalary.objects.count(), 0)


    def test_teacher_can_list_only_own_monthly_salaries(self):
        other_teacher = User.objects.create_user(
            username="other_teacher",
            role=User.Role.TEACHER,
        )

        own_salary = MonthlySalary.objects.create(
            teacher=self.teacher,
            year=2026,
            month=9,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("200.00"),
            total_penalty_amount=Decimal("20.00"),
            net_amount=Decimal("180.00"),
        )

        MonthlySalary.objects.create(
            teacher=other_teacher,
            year=2026,
            month=9,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("300.00"),
            total_penalty_amount=Decimal("0.00"),
            net_amount=Decimal("300.00"),
        )

        self.client.force_authenticate(
            user=self.teacher
        )

        url = reverse("monthly-salary-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            own_salary.id,
        )


    def test_finance_officer_can_list_all_monthly_salaries(self):
        MonthlySalary.objects.create(
            teacher=self.teacher,
            year=2026,
            month=9,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("200.00"),
            total_penalty_amount=Decimal("0.00"),
            net_amount=Decimal("200.00"),
        )

        other_teacher = User.objects.create_user(
            username="other_teacher",
            role=User.Role.TEACHER,
        )

        MonthlySalary.objects.create(
            teacher=other_teacher,
            year=2026,
            month=9,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("300.00"),
            total_penalty_amount=Decimal("0.00"),
            net_amount=Decimal("300.00"),
        )

        self.client.force_authenticate(
            user=self.finance_officer
        )

        url = reverse("monthly-salary-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


    def test_finance_officer_can_filter_salaries_by_year_and_month(self):
        september_salary = MonthlySalary.objects.create(
            teacher=self.teacher,
            year=2026,
            month=9,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("200.00"),
            total_penalty_amount=Decimal("0.00"),
            net_amount=Decimal("200.00"),
        )

        MonthlySalary.objects.create(
            teacher=self.teacher,
            year=2026,
            month=10,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("300.00"),
            total_penalty_amount=Decimal("0.00"),
            net_amount=Decimal("300.00"),
        )

        self.client.force_authenticate(
            user=self.finance_officer
        )

        url = reverse("monthly-salary-list")

        response = self.client.get(
            url,
            {
                "year": 2026,
                "month": 9,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            september_salary.id,
        )


    def test_education_officer_cannot_list_monthly_salaries(self):
        education_officer = User.objects.create_user(
            username="salary_education",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.client.force_authenticate(
            user=education_officer
        )

        url = reverse("monthly-salary-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


    def test_anonymous_user_cannot_list_monthly_salaries(self):
        url = reverse("monthly-salary-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 401)


    def test_teacher_cannot_retrieve_another_teachers_salary(self):
        other_teacher = User.objects.create_user(
            username="other_salary_teacher",
            role=User.Role.TEACHER,
        )

        other_salary = MonthlySalary.objects.create(
            teacher=other_teacher,
            year=2026,
            month=9,
            calculated_by=self.finance_officer,
            gross_amount=Decimal("300.00"),
            total_penalty_amount=Decimal("0.00"),
            net_amount=Decimal("300.00"),
        )

        self.client.force_authenticate(
            user=self.teacher
        )

        url = reverse("monthly-salary-detail", args=[other_salary.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


    def test_finance_officer_can_calculate_salary_for_one_teacher(self):
        second_teacher = User.objects.create_user(
            username="second_salary_teacher",
            role=User.Role.TEACHER,
        )

        TeacherTermWage.objects.create(
            teacher=second_teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("300.00"),
        )

        first_session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 10, 10, 0)
            ),
            session_number=1,
        )

        second_session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=second_teacher,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 20, 10, 0)
            ),
            session_number=2,
        )

        SessionReport.objects.create(
            session=first_session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="First teacher lesson",
            present_count=10,
            absent_count=0,
            submitted_at=timezone.make_aware(
                datetime(2026, 9, 10, 12, 0)
            ),
        )

        SessionReport.objects.create(
            session=second_session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Second teacher lesson",
            present_count=10,
            absent_count=0,
            submitted_at=timezone.make_aware(
                datetime(2026, 9, 20, 12, 0)
            ),
        )

        self.client.force_authenticate(
            user=self.finance_officer
        )

        url = reverse(
            "monthly-salary-calculate-teacher"
        )

        response = self.client.post(
            url,
            {
                "teacher": self.teacher.id,
                "year": 2026,
                "month": 9,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            MonthlySalary.objects.count(),
            1,
        )

        salary = MonthlySalary.objects.get()

        self.assertEqual(
            salary.teacher,
            self.teacher,
        )

        self.assertEqual(
            salary.net_amount,
            Decimal("200.00"),
        )


    def test_teacher_cannot_calculate_single_teacher_salary(self):
        self.client.force_authenticate(
            user=self.teacher
        )

        url = reverse("monthly-salary-calculate-teacher")

        response = self.client.post(
            url,
            {
                "teacher": self.teacher.id,
                "year": 2026,
                "month": 9,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            MonthlySalary.objects.count(),
            0,
        )


    def test_cannot_calculate_teacher_salary_when_month_is_not_ready(self):
        second_teacher = User.objects.create_user(
            username="pending_report_teacher",
            role=User.Role.TEACHER,
        )

        approved_session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=self.teacher,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 10, 10, 0)
            ),
            session_number=1,
        )

        pending_session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=second_teacher,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 20, 10, 0)
            ),
            session_number=2,
        )

        SessionReport.objects.create(
            session=approved_session,
            status=SessionReport.Status.APPROVED,
            lesson_summary="Approved lesson",
            present_count=10,
            absent_count=0,
            submitted_at=timezone.make_aware(
                datetime(2026, 9, 10, 12, 0)
            ),
        )

        SessionReport.objects.create(
            session=pending_session,
            status=SessionReport.Status.PENDING,
            lesson_summary="Pending lesson",
            present_count=10,
            absent_count=0,
            submitted_at=timezone.make_aware(
                datetime(2026, 9, 20, 12, 0)
            ),
        )

        self.client.force_authenticate(
            user=self.finance_officer
        )

        url = reverse(
            "monthly-salary-calculate-teacher"
        )

        response = self.client.post(
            url,
            {
                "teacher": self.teacher.id,
                "year": 2026,
                "month": 9,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            MonthlySalary.objects.count(),
            0,
        )