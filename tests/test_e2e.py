from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class FullWorkflowE2ETests(APITestCase):

    def setUp(self):
        cache.clear()

        self.password = "Test123@"

        self.teacher = User.objects.create_user(
            username="e2e_teacher",
            password=self.password,
            first_name="E2E",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07111111111",
            emergency_phone_number="07222222222",
        )

        self.education_officer = User.objects.create_user(
            username="e2e_education",
            password=self.password,
            first_name="E2E",
            last_name="Education",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.finance_officer = User.objects.create_user(
            username="e2e_finance",
            password=self.password,
            first_name="E2E",
            last_name="Finance",
            role=User.Role.FINANCE_OFFICER,
        )

    def get_access_token(self, user):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": user.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        return response.data["access"]

    def authenticate(self, token):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

    def test_full_reporting_and_payroll_workflow(self):
        teacher_token = self.get_access_token(self.teacher)
        education_token = self.get_access_token(
            self.education_officer
        )
        finance_token = self.get_access_token(
            self.finance_officer
        )

        today = timezone.localdate()

        current_month_start = today.replace(day=1)
        previous_month_last_day = (
            current_month_start - timedelta(days=1)
        )
        term_start = previous_month_last_day.replace(day=1)

        if today.month == 12:
            next_month_start = date(
                today.year + 1,
                1,
                1,
            )
        else:
            next_month_start = date(
                today.year,
                today.month + 1,
                1,
            )

        term_end = next_month_start - timedelta(days=1)

        session_datetime = timezone.now() - timedelta(hours=2)

        # Education officer creates a school
        self.authenticate(education_token)

        school_response = self.client.post(
            reverse("school-list"),
            {
                "name": "E2E School",
                "address": "London",
            },
            format="json",
        )

        self.assertEqual(
            school_response.status_code,
            status.HTTP_201_CREATED,
        )

        school_id = school_response.data["id"]

        # Education officer creates a term
        term_response = self.client.post(
            reverse("term-list"),
            {
                "start_date": term_start.isoformat(),
                "end_date": term_end.isoformat(),
                "term_type": "regular",
            },
            format="json",
        )

        self.assertEqual(
            term_response.status_code,
            status.HTTP_201_CREATED,
        )

        term_id = term_response.data["id"]

        # Education officer creates a class
        class_response = self.client.post(
            reverse("course-class-list"),
            {
                "school": school_id,
                "term": term_id,
                "title": "Python",
                "class_code": "E2E101",
                "start_date": term_start.isoformat(),
                "end_date": term_end.isoformat(),
                "session_duration": 90,
            },
            format="json",
        )

        self.assertEqual(
            class_response.status_code,
            status.HTTP_201_CREATED,
        )

        course_class_id = class_response.data["id"]

        # Education officer assigns the teacher
        assignment_response = self.client.post(
            reverse("teacher-class-assignment-list"),
            {
                "teacher": self.teacher.id,
                "course_class": course_class_id,
                "start_date": term_start.isoformat(),
                "end_date": term_end.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            assignment_response.status_code,
            status.HTTP_201_CREATED,
        )

        # Education officer creates a session
        session_response = self.client.post(
            reverse("course-session-list"),
            {
                "course_class": course_class_id,
                "session_datetime": session_datetime.isoformat(),
                "session_number": 1,
            },
            format="json",
        )

        self.assertEqual(
            session_response.status_code,
            status.HTTP_201_CREATED,
        )

        session_id = session_response.data["id"]

        # Teacher submits the session report
        self.authenticate(teacher_token)

        report_response = self.client.post(
            reverse("session-report-list"),
            {
                "session": session_id,
                "lesson_summary": "Python fundamentals",
                "present_count": 10,
                "absent_count": 2,
            },
            format="json",
        )

        self.assertEqual(
            report_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            report_response.data["status"],
            "pending",
        )

        report_id = report_response.data["id"]

        # Education officer approves the report
        self.authenticate(education_token)

        review_response = self.client.post(
            reverse(
                "session-report-review",
                args=[report_id],
            ),
            {
                "status": "approved",
                "review_note": "",
            },
            format="json",
        )

        self.assertEqual(
            review_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            review_response.data["status"],
            "approved",
        )

        self.assertEqual(
            review_response.data["late_hours"],
            0,
        )

        # Finance officer sets the teacher wage
        self.authenticate(finance_token)

        wage_response = self.client.post(
            reverse("teacher-term-wage-list"),
            {
                "teacher": self.teacher.id,
                "term": term_id,
                "base_wage_rate": "200.00",
            },
            format="json",
        )

        self.assertEqual(
            wage_response.status_code,
            status.HTTP_201_CREATED,
        )

        # Finance officer calculates the teacher's salary
        salary_response = self.client.post(
            reverse("monthly-salary-calculate-teacher"),
            {
                "teacher": self.teacher.id,
                "year": session_datetime.year,
                "month": session_datetime.month,
            },
            format="json",
        )

        self.assertEqual(
            salary_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            salary_response.data["gross_amount"],
            "200.00",
        )

        self.assertEqual(
            salary_response.data["total_penalty_amount"],
            "0.00",
        )

        self.assertEqual(
            salary_response.data["net_amount"],
            "200.00",
        )

        # Teacher can see the calculated salary
        self.authenticate(teacher_token)

        salary_list_response = self.client.get(
            reverse("monthly-salary-list"),
            {
                "year": session_datetime.year,
                "month": session_datetime.month,
            },
        )

        self.assertEqual(
            salary_list_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(salary_list_response.data),
            1,
        )

        self.assertEqual(
            salary_list_response.data[0]["teacher"],
            self.teacher.id,
        )

        self.assertEqual(
            salary_list_response.data[0]["net_amount"],
            "200.00",
        )