from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from academics.models import (
    CourseClass,
    CourseSession,
    School,
    TeacherClassAssignment,
    Term,
)
from reports.models import SessionReport

User = get_user_model()


class SessionReportAPITests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher",
            first_name="Test",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07111111111",
            emergency_phone_number="07222222222",
        )

        self.education_officer = User.objects.create_user(
            username="education",
            first_name="Test",
            last_name="Education",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.finance_officer = User.objects.create_user(
            username="finance",
            first_name="Test",
            last_name="Finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.school = School.objects.create(
            name="Test School",
            address="London",
        )

        self.term = Term.objects.create(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            term_type=Term.TermType.REGULAR,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="PY101",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            session_duration=90,
        )

        self.assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
        )

        self.session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 10, 10, 0)
            ),
            session_number=1,
        )

        self.url = reverse("session-report-list")


    def test_teacher_can_create_report_for_own_session(self):
        self.client.force_authenticate(user=self.teacher)

        data = {
            "session": self.session.id,
            "lesson_summary": "Python basics",
            "present_count": 10,
            "absent_count": 2,
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(SessionReport.objects.count(), 1)

        report = SessionReport.objects.get()
        self.assertEqual(report.session, self.session)
        self.assertEqual(report.status, SessionReport.Status.PENDING)


    def test_teacher_cannot_create_report_for_another_teachers_session(self):
        other_teacher = User.objects.create_user(
            username="other_teacher",
            first_name="Other",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07333333333",
            emergency_phone_number="07444444444",
        )

        other_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django",
            class_code="DJ101",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            session_duration=90,
        )

        TeacherClassAssignment.objects.create(
            teacher=other_teacher,
            course_class=other_course_class,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
        )

        other_session = CourseSession.objects.create(
            course_class=other_course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 12, 10, 0)
            ),
            session_number=1,
        )

        self.client.force_authenticate(user=self.teacher)

        data = {
            "session": other_session.id,
            "lesson_summary": "Django basics",
            "present_count": 8,
            "absent_count": 1,
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(SessionReport.objects.count(), 0)