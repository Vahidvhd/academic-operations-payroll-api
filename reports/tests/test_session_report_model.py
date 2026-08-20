from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from academics.models import CourseClass, CourseSession, School, Term
from reports.models import SessionReport

User = get_user_model()


class SessionReportModelTests(TestCase):
    def setUp(self):
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
            session_duration=CourseClass.SessionDuration.NINETY,
        )

        self.session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 10, 10, 0)
            ),
            session_number=1,
        )

        self.education_officer = User.objects.create_user(
            username="education1",
            password="testpass123",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.teacher = User.objects.create_user(
            username="teacher1",
            password="testpass123",
            role=User.Role.TEACHER,
        )


    def test_report_cannot_be_submitted_before_session_ends(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 11, 29)
            ),
        )

        self.assertRaises(ValidationError, report.full_clean)


    def test_report_can_be_submitted_when_session_ends(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 11, 30)
            ),
        )

        report.full_clean()


    def test_rejected_report_requires_review_note(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
            status=SessionReport.Status.REJECTED,
            reviewed_by=self.education_officer,
        )

        self.assertRaises(ValidationError, report.full_clean)


    def test_approved_report_requires_reviewer(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
            status=SessionReport.Status.APPROVED,
        )

        self.assertRaises(ValidationError, report.full_clean)


    def test_reviewer_must_be_education_officer(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
            status=SessionReport.Status.APPROVED,
            reviewed_by=self.teacher,
        )

        self.assertRaises(ValidationError, report.full_clean)


    def test_approved_report_with_education_officer_is_valid(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
            status=SessionReport.Status.APPROVED,
            reviewed_by=self.education_officer,
        )

        report.full_clean()


    def test_rejected_report_with_review_note_is_valid(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
            status=SessionReport.Status.REJECTED,
            reviewed_by=self.education_officer,
            review_note="Attendance needs correction.",
        )

        report.full_clean()


    def test_rejected_report_requires_reviewer(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
            status=SessionReport.Status.REJECTED,
            review_note="Attendance needs correction.",
        )

        self.assertRaises(ValidationError, report.full_clean)


    def test_report_approved_at_exactly_48_hours_is_not_late(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
        )

        session_end = (
            self.session.session_datetime
            + timedelta(minutes=self.course_class.session_duration)
        )

        approved_at = session_end + timedelta(hours=48)

        self.assertEqual(
            report.calculate_late_hours(approved_at),
            0,
        )


    def test_report_approved_one_second_after_48_hours_has_one_late_hour(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
        )

        session_end = (
            self.session.session_datetime
            + timedelta(minutes=self.course_class.session_duration)
        )

        approved_at = session_end + timedelta(hours=48, seconds=1)

        self.assertEqual(report.calculate_late_hours(approved_at), 1)


    def test_report_one_full_hour_late_has_one_late_hour(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
        )

        session_end = (
            self.session.session_datetime
            + timedelta(minutes=self.course_class.session_duration)
        )

        approved_at = session_end + timedelta(hours=49)

        self.assertEqual(report.calculate_late_hours(approved_at), 1)


    def test_report_more_than_one_full_hour_late_has_two_late_hours(self):
        report = SessionReport(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.make_aware(
                datetime(2026, 8, 10, 12, 0)
            ),
        )

        session_end = (
            self.session.session_datetime
            + timedelta(minutes=self.course_class.session_duration)
        )

        approved_at = session_end + timedelta(hours=49, seconds=1)

        self.assertEqual(report.calculate_late_hours(approved_at), 2)