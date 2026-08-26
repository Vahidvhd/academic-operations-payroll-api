from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import (
    CourseClass,
    CourseSession,
    School,
    TeacherClassAssignment,
    Term,
)
from academics.services import filter_sessions_for_teacher

User = get_user_model()


class FilterSessionsForTeacherTests(TestCase):
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
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            term_type=Term.TermType.REGULAR,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="PY101",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            session_duration=90,
        )

        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
        )

    def test_returns_session_for_assigned_teacher(self):
        session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        queryset = CourseSession.objects.filter(
            is_deleted=False,
        )

        result = filter_sessions_for_teacher(
            queryset,
            self.teacher.id,
        )

        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), session)


    def test_returns_session_for_substitute_teacher(self):
        substitute_teacher = User.objects.create_user(
            username="substitute_teacher",
            role=User.Role.TEACHER,
        )

        session = CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=substitute_teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        queryset = CourseSession.objects.filter(
            is_deleted=False,
        )

        result = filter_sessions_for_teacher(
            queryset,
            substitute_teacher.id,
        )

        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), session)


    def test_excludes_session_from_assigned_teacher_when_substitute_exists(self):
        substitute_teacher = User.objects.create_user(
            username="substitute_teacher_hidden",
            role=User.Role.TEACHER,
        )

        CourseSession.objects.create(
            course_class=self.course_class,
            conducted_by=substitute_teacher,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        queryset = CourseSession.objects.filter(
            is_deleted=False,
        )

        result = filter_sessions_for_teacher(
            queryset,
            self.teacher.id,
        )

        self.assertEqual(result.count(), 0)