from datetime import date, datetime

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