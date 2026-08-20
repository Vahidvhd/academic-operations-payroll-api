from datetime import date, datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from academics.models import (
    CourseClass,
    CourseSession,
    School,
    TeacherClassAssignment,
    Term,
)
from reports.serializers import SessionReportSerializer

User = get_user_model()


class SessionReportSerializerTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher1",
            password="testpass123",
            role=User.Role.TEACHER,
        )

        self.school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

        self.term = Term.objects.create(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            term_type=Term.TermType.SUMMER,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY-101",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            session_duration=90,
        )

        self.assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 8, 1),
        )

        self.session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(datetime(2026, 8, 10, 10, 0)),
            session_number=1,
        )

        self.factory = APIRequestFactory()
        self.request = self.factory.post("/reports/")
        self.request.user = self.teacher


    def test_teacher_can_report_own_assigned_session(self):
        serializer = SessionReportSerializer(
            data={
                "session": self.session.id,
                "lesson_summary": "Introduction to Python",
                "present_count": 10,
                "absent_count": 2,
            },
            context={"request": self.request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)


    def test_teacher_cannot_report_session_from_another_assignment(self):
        other_teacher = User.objects.create_user(
            username="teacher2",
            password="testpass123",
            role=User.Role.TEACHER,
        )

        self.request.user = other_teacher

        serializer = SessionReportSerializer(
            data={
                "session": self.session.id,
                "lesson_summary": "Introduction to Python",
                "present_count": 10,
                "absent_count": 2,
            },
            context={"request": self.request},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("session", serializer.errors)


    @patch("reports.serializers.timezone.now")
    def test_submitted_at_is_set_by_backend(self, mocked_now):
        fixed_time = timezone.make_aware(
            datetime(2026, 8, 10, 12, 0)
        )
        mocked_now.return_value = fixed_time

        serializer = SessionReportSerializer(
            data={
                "session": self.session.id,
                "lesson_summary": "Introduction to Python",
                "present_count": 10,
                "absent_count": 2,
            },
            context={"request": self.request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        report = serializer.save()

        self.assertEqual(report.submitted_at, fixed_time)

    def test_cannot_report_soft_deleted_session(self):
        self.session.is_deleted = True
        self.session.save()

        serializer = SessionReportSerializer(
            data={
                "session": self.session.id,
                "lesson_summary": "Introduction to Python",
                "present_count": 10,
                "absent_count": 2,
            },
            context={"request": self.request},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("session", serializer.errors)