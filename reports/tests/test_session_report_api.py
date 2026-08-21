from datetime import date, datetime
from unittest.mock import patch

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
from reports.models import ReportStatusHistory, SessionReport

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



    @patch("reports.serializers.timezone")
    def test_teacher_cannot_create_report_before_session_ends(
        self,
        mock_timezone,
    ):
        mock_timezone.now.return_value = timezone.make_aware(
            datetime(2026, 8, 10, 11, 29)
        )

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

        self.assertEqual(response.status_code, 400)
        self.assertIn("session", response.data)
        self.assertEqual(SessionReport.objects.count(), 0)


    def test_teacher_cannot_create_second_report_for_same_session(self):
        SessionReport.objects.create(
            session=self.session,
            lesson_summary="First report",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.teacher)

        data = {
            "session": self.session.id,
            "lesson_summary": "Second report",
            "present_count": 9,
            "absent_count": 3,
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("session", response.data)
        self.assertEqual(SessionReport.objects.count(), 1)

    def test_teacher_cannot_create_report_with_negative_attendance(self):
        self.client.force_authenticate(user=self.teacher)

        data = {
            "session": self.session.id,
            "lesson_summary": "Python basics",
            "present_count": -1,
            "absent_count": -1,
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("present_count", response.data)
        self.assertIn("absent_count", response.data)
        self.assertEqual(SessionReport.objects.count(), 0)
        

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


    def test_teacher_only_sees_own_reports(self):
        own_report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        other_teacher = User.objects.create_user(
            username="list_other_teacher",
            first_name="Other",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07555555555",
            emergency_phone_number="07666666666",
        )

        other_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django",
            class_code="DJ102",
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

        SessionReport.objects.create(
            session=other_session,
            lesson_summary="Django basics",
            present_count=8,
            absent_count=1,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.teacher)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], own_report.id)


    def test_education_officer_can_see_all_reports(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], report.id)


    def test_finance_officer_cannot_access_reports(self):
        self.client.force_authenticate(user=self.finance_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)


    def test_anonymous_user_cannot_access_reports(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)


    def test_teacher_cannot_retrieve_another_teachers_report(self):
        other_teacher = User.objects.create_user(
            username="detail_other_teacher",
            first_name="Other",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07777777777",
            emergency_phone_number="07888888888",
        )

        other_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django Advanced",
            class_code="DJ103",
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

        other_report = SessionReport.objects.create(
            session=other_session,
            lesson_summary="Django advanced",
            present_count=8,
            absent_count=1,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-detail", args=[other_report.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


    def test_education_officer_can_retrieve_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("session-report-detail", args=[report.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], report.id)


    def test_teacher_can_resubmit_rejected_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Old summary",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.REJECTED,
            submitted_at=timezone.now(),
            reviewed_by=self.education_officer,
            review_note="Please update the summary.",
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-detail", args=[report.id])

        data = {
            "lesson_summary": "Updated summary",
            "present_count": 11,
            "absent_count": 1,
        }

        response = self.client.patch(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.lesson_summary, "Updated summary")
        self.assertEqual(report.present_count, 11)
        self.assertEqual(report.absent_count, 1)
        self.assertEqual(report.status, SessionReport.Status.PENDING)
        self.assertEqual(ReportStatusHistory.objects.count(), 1)

        history = ReportStatusHistory.objects.get()

        self.assertEqual(history.session_report, report)
        self.assertEqual(history.changed_by, self.teacher)
        self.assertEqual(history.old_status, SessionReport.Status.REJECTED)
        self.assertEqual(history.new_status, SessionReport.Status.PENDING)
        self.assertEqual(history.note, "")


    def test_teacher_cannot_change_session_when_resubmitting_report(self):
        second_session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 12, 10, 0)
            ),
            session_number=2,
        )

        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Old summary",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.REJECTED,
            submitted_at=timezone.now(),
            reviewed_by=self.education_officer,
            review_note="Please update.",
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse(
            "session-report-detail",
            args=[report.id],
        )

        response = self.client.patch(
            url,
            {"session": second_session.id},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        report.refresh_from_db()

        self.assertEqual(report.session, self.session)
        self.assertEqual(report.status, SessionReport.Status.REJECTED)


    def test_teacher_cannot_edit_pending_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.PENDING,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-detail", args=[report.id])

        data = {
            "lesson_summary": "Updated summary",
        }

        response = self.client.patch(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        report.refresh_from_db()
        self.assertEqual(report.lesson_summary, "Python basics")


    def test_teacher_cannot_edit_approved_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.APPROVED,
            submitted_at=timezone.now(),
            reviewed_by=self.education_officer,
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-detail", args=[report.id])

        data = {
            "lesson_summary": "Updated summary",
        }

        response = self.client.patch(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        report.refresh_from_db()
        self.assertEqual(report.lesson_summary, "Python basics")


    def test_teacher_cannot_edit_another_teachers_rejected_report(self):
        other_teacher = User.objects.create_user(
            username="edit_other_teacher",
            first_name="Other",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07999999999",
            emergency_phone_number="07000000000",
        )

        other_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django REST",
            class_code="DJ104",
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

        report = SessionReport.objects.create(
            session=other_session,
            lesson_summary="Old summary",
            present_count=8,
            absent_count=1,
            status=SessionReport.Status.REJECTED,
            submitted_at=timezone.now(),
            reviewed_by=self.education_officer,
            review_note="Please update.",
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-detail", args=[report.id])

        data = {
            "lesson_summary": "Updated summary",
        }

        response = self.client.patch(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 404)

        report.refresh_from_db()
        self.assertEqual(report.lesson_summary, "Old summary")

    def test_education_officer_cannot_edit_report_content(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("session-report-detail", args=[report.id])

        data = {
            "lesson_summary": "Changed by officer",
        }

        response = self.client.patch(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        report.refresh_from_db()
        self.assertEqual(report.lesson_summary, "Python basics")


    def test_session_report_cannot_be_deleted(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse(
            "session-report-detail",
            args=[report.id],
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            SessionReport.objects.filter(id=report.id).exists()
        )


    def test_education_officer_can_reject_pending_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("session-report-review", args=[report.id])

        data = {
            "status": SessionReport.Status.REJECTED,
            "review_note": "Please add more detail.",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.REJECTED)
        self.assertEqual(report.review_note, "Please add more detail.")
        self.assertEqual(report.reviewed_by, self.education_officer)
        self.assertEqual(ReportStatusHistory.objects.count(), 1)

        history = ReportStatusHistory.objects.get()

        self.assertEqual(history.session_report, report)
        self.assertEqual(history.changed_by, self.education_officer)
        self.assertEqual(history.old_status, SessionReport.Status.PENDING)
        self.assertEqual(history.new_status, SessionReport.Status.REJECTED)
        self.assertEqual(history.note, "Please add more detail.")

    def test_education_officer_cannot_reject_without_review_note(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("session-report-review", args=[report.id])

        data = {
            "status": SessionReport.Status.REJECTED,
            "review_note": "",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        report.refresh_from_db()
        self.assertEqual(report.status, SessionReport.Status.PENDING)


    def test_education_officer_cannot_set_review_status_to_pending(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse(
            "session-report-review",
            args=[report.id],
        )

        response = self.client.post(
            url,
            {
                "status": SessionReport.Status.PENDING,
                "review_note": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.data)

        report.refresh_from_db()
        self.assertEqual(report.status, SessionReport.Status.PENDING)


    def test_education_officer_can_approve_pending_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("session-report-review", args=[report.id])

        data = {
            "status": SessionReport.Status.APPROVED,
            "review_note": "Looks good.",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.APPROVED)
        self.assertEqual(report.reviewed_by, self.education_officer)
        self.assertEqual(report.review_note, "Looks good.")

        self.assertEqual(ReportStatusHistory.objects.count(), 1)

        history = ReportStatusHistory.objects.get()

        self.assertEqual(history.session_report, report)
        self.assertEqual(history.changed_by, self.education_officer)
        self.assertEqual(history.old_status, SessionReport.Status.PENDING)
        self.assertEqual(history.new_status, SessionReport.Status.APPROVED)
        self.assertEqual(history.note, "Looks good.")


    def test_education_officer_can_approve_rejected_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.REJECTED,
            submitted_at=timezone.now(),
            reviewed_by=self.education_officer,
            review_note="Needs review.",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("session-report-review", args=[report.id])

        data = {
            "status": SessionReport.Status.APPROVED,
            "review_note": "Approved after review.",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.APPROVED)
        self.assertEqual(report.reviewed_by, self.education_officer)
        self.assertEqual(report.review_note, "Approved after review.")

        self.assertEqual(ReportStatusHistory.objects.count(), 1)

        history = ReportStatusHistory.objects.get()

        self.assertEqual(history.session_report, report)
        self.assertEqual(history.changed_by, self.education_officer)
        self.assertEqual(history.old_status, SessionReport.Status.REJECTED)
        self.assertEqual(history.new_status, SessionReport.Status.APPROVED)
        self.assertEqual(history.note, "Approved after review.")


    def test_education_officer_cannot_reject_rejected_report_again(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.REJECTED,
            submitted_at=timezone.now(),
            reviewed_by=self.education_officer,
            review_note="Original rejection reason.",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse(
            "session-report-review",
            args=[report.id],
        )

        response = self.client.post(
            url,
            {
                "status": SessionReport.Status.REJECTED,
                "review_note": "Another rejection reason.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.REJECTED)
        self.assertEqual(
            report.review_note,
            "Original rejection reason.",
        )


    def test_approved_report_cannot_be_reviewed_again(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.APPROVED,
            submitted_at=timezone.now(),
            reviewed_by=self.education_officer,
            review_note="Approved.",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("session-report-review", args=[report.id])

        data = {
            "status": SessionReport.Status.REJECTED,
            "review_note": "Changed my mind.",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        report.refresh_from_db()
        self.assertEqual(report.status, SessionReport.Status.APPROVED)


    def test_teacher_cannot_review_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-review", args=[report.id])

        data = {
            "status": SessionReport.Status.APPROVED,
            "review_note": "Approved by teacher.",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        report.refresh_from_db()
        self.assertEqual(report.status, SessionReport.Status.PENDING)


    def test_finance_officer_cannot_review_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.finance_officer)

        url = reverse("session-report-review", args=[report.id])

        data = {
            "status": SessionReport.Status.APPROVED,
            "review_note": "Approved.",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        report.refresh_from_db()
        self.assertEqual(report.status, SessionReport.Status.PENDING)


    def test_anonymous_user_cannot_review_report(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        url = reverse("session-report-review", args=[report.id])

        data = {
            "status": SessionReport.Status.APPROVED,
            "review_note": "Approved.",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 401)

        report.refresh_from_db()
        self.assertEqual(report.status, SessionReport.Status.PENDING)


    @patch("reports.views.timezone")
    def test_approval_calculates_late_hours_from_session_end(
        self,
        mock_timezone,
    ):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        approval_time = timezone.make_aware(
            datetime(2026, 8, 12, 12, 30)
        )

        mock_timezone.now.return_value = approval_time

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("session-report-review", args=[report.id])

        data = {
            "status": SessionReport.Status.APPROVED,
            "review_note": "Approved.",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.APPROVED)
        self.assertEqual(report.late_hours, 1)


    @patch("reports.views.timezone")
    def test_resubmission_does_not_reset_late_hours_timer(
        self,
        mock_timezone,
    ):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Old summary",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.REJECTED,
            submitted_at=timezone.now(),
            reviewed_by=self.education_officer,
            review_note="Please update.",
        )

        self.client.force_authenticate(user=self.teacher)

        detail_url = reverse(
            "session-report-detail",
            args=[report.id],
        )

        response = self.client.patch(
            detail_url,
            {
                "lesson_summary": "Updated summary",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.PENDING)
        self.assertEqual(report.lesson_summary, "Updated summary")

        approval_time = timezone.make_aware(
            datetime(2026, 8, 14, 12, 30)
        )

        mock_timezone.now.return_value = approval_time

        self.client.force_authenticate(user=self.education_officer)

        review_url = reverse(
            "session-report-review",
            args=[report.id],
        )

        response = self.client.post(
            review_url,
            {
                "status": SessionReport.Status.APPROVED,
                "review_note": "Approved.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.APPROVED)
        self.assertEqual(report.late_hours, 49)


    def test_education_officer_can_filter_reports_by_school(self):
        first_report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        other_school = School.objects.create(
            name="Other School",
            address="Manchester",
        )

        other_course_class = CourseClass.objects.create(
            school=other_school,
            term=self.term,
            title="Django",
            class_code="DJ105",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            session_duration=90,
        )

        other_session = CourseSession.objects.create(
            course_class=other_course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 12, 10, 0)
            ),
            session_number=1,
        )

        SessionReport.objects.create(
            session=other_session,
            lesson_summary="Django basics",
            present_count=8,
            absent_count=1,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {"school": self.school.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], first_report.id)


    def test_education_officer_can_filter_reports_by_course_class(self):
        first_report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        other_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django",
            class_code="DJ106",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            session_duration=90,
        )

        other_session = CourseSession.objects.create(
            course_class=other_course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 12, 10, 0)
            ),
            session_number=1,
        )

        SessionReport.objects.create(
            session=other_session,
            lesson_summary="Django basics",
            present_count=8,
            absent_count=1,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {"course_class": self.course_class.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], first_report.id)


    def test_education_officer_can_filter_reports_by_teacher(self):
        first_report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        other_teacher = User.objects.create_user(
            username="filter_other_teacher",
            first_name="Other",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07123456789",
            emergency_phone_number="07987654321",
        )

        other_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django",
            class_code="DJ107",
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

        SessionReport.objects.create(
            session=other_session,
            lesson_summary="Django basics",
            present_count=8,
            absent_count=1,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {"teacher": self.teacher.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], first_report.id)


    def test_education_officer_can_filter_reports_by_date_from(self):
        SessionReport.objects.create(
            session=self.session,
            lesson_summary="Old report",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        later_session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 20, 10, 0)
            ),
            session_number=2,
        )

        later_report = SessionReport.objects.create(
            session=later_session,
            lesson_summary="Later report",
            present_count=9,
            absent_count=3,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {"date_from": "2026-08-15"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], later_report.id)


    def test_education_officer_can_filter_reports_by_date_to(self):
        early_report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Early report",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        later_session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 20, 10, 0)
            ),
            session_number=2,
        )

        SessionReport.objects.create(
            session=later_session,
            lesson_summary="Later report",
            present_count=9,
            absent_count=3,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {"date_to": "2026-08-15"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], early_report.id)


    def test_teacher_filter_uses_assignment_date(self):
        second_teacher = User.objects.create_user(
            username="historical_teacher",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07101010101",
            emergency_phone_number="07202020202",
        )

        self.assignment.end_date = date(2026, 8, 15)
        self.assignment.save()

        TeacherClassAssignment.objects.create(
            teacher=second_teacher,
            course_class=self.course_class,
            start_date=date(2026, 8, 16),
            end_date=date(2026, 8, 31),
        )

        first_report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="First teacher report",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        second_session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 20, 10, 0)
            ),
            session_number=2,
        )

        SessionReport.objects.create(
            session=second_session,
            lesson_summary="Second teacher report",
            present_count=9,
            absent_count=3,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {"teacher": self.teacher.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], first_report.id)


    def test_education_officer_can_combine_report_filters(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {
                "school": self.school.id,
                "teacher": self.teacher.id,
                "date_from": "2026-08-01",
                "date_to": "2026-08-15",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], report.id)


    def test_teacher_filter_params_do_not_bypass_ownership(self):
        own_report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        other_teacher = User.objects.create_user(
            username="filter_bypass_teacher",
            first_name="Other",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07111112222",
            emergency_phone_number="07222223333",
        )

        other_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django",
            class_code="DJ108",
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

        SessionReport.objects.create(
            session=other_session,
            lesson_summary="Django basics",
            present_count=8,
            absent_count=1,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.teacher)

        response = self.client.get(
            self.url,
            {"teacher": other_teacher.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], own_report.id)


    def test_education_officer_can_view_report_status_history(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        ReportStatusHistory.objects.create(
            session_report=report,
            changed_by=self.education_officer,
            old_status=SessionReport.Status.PENDING,
            new_status=SessionReport.Status.REJECTED,
            note="Please add more detail.",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse(
            "session-report-history",
            args=[report.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]["old_status"],
            SessionReport.Status.PENDING,
        )
        self.assertEqual(
            response.data[0]["new_status"],
            SessionReport.Status.REJECTED,
        )
        self.assertEqual(
            response.data[0]["changed_by"],
            self.education_officer.id,
        )
        self.assertEqual(
            response.data[0]["note"],
            "Please add more detail.",
        )


    def test_teacher_cannot_view_report_status_history(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        ReportStatusHistory.objects.create(
            session_report=report,
            changed_by=self.education_officer,
            old_status=SessionReport.Status.PENDING,
            new_status=SessionReport.Status.REJECTED,
            note="Please add more detail.",
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse(
            "session-report-history",
            args=[report.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


    def test_finance_officer_cannot_view_report_status_history(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        ReportStatusHistory.objects.create(
            session_report=report,
            changed_by=self.education_officer,
            old_status=SessionReport.Status.PENDING,
            new_status=SessionReport.Status.REJECTED,
            note="Please add more detail.",
        )

        self.client.force_authenticate(user=self.finance_officer)

        url = reverse(
            "session-report-history",
            args=[report.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


    def test_anonymous_user_cannot_view_report_status_history(self):
        report = SessionReport.objects.create(
            session=self.session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        ReportStatusHistory.objects.create(
            session_report=report,
            changed_by=self.education_officer,
            old_status=SessionReport.Status.PENDING,
            new_status=SessionReport.Status.REJECTED,
            note="Please add more detail.",
        )

        url = reverse(
            "session-report-history",
            args=[report.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 401)


    def test_full_session_report_workflow(self):
        self.client.force_authenticate(user=self.teacher)

        create_data = {
            "session": self.session.id,
            "lesson_summary": "Python basics",
            "present_count": 10,
            "absent_count": 2,
        }

        create_response = self.client.post(
            self.url,
            create_data,
            format="json",
        )

        self.assertEqual(create_response.status_code, 201)

        report = SessionReport.objects.get()

        self.assertEqual(report.status, SessionReport.Status.PENDING)

        self.client.force_authenticate(user=self.education_officer)

        review_url = reverse(
            "session-report-review",
            args=[report.id],
        )

        reject_response = self.client.post(
            review_url,
            {
                "status": SessionReport.Status.REJECTED,
                "review_note": "Please add more detail.",
            },
            format="json",
        )

        self.assertEqual(reject_response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.REJECTED)

        self.client.force_authenticate(user=self.teacher)

        detail_url = reverse(
            "session-report-detail",
            args=[report.id],
        )

        resubmit_response = self.client.patch(
            detail_url,
            {
                "lesson_summary": "Updated Python basics",
                "present_count": 11,
                "absent_count": 1,
            },
            format="json",
        )

        self.assertEqual(resubmit_response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.PENDING)
        self.assertEqual(report.lesson_summary, "Updated Python basics")

        self.client.force_authenticate(user=self.education_officer)

        approve_response = self.client.post(
            review_url,
            {
                "status": SessionReport.Status.APPROVED,
                "review_note": "Approved.",
            },
            format="json",
        )

        self.assertEqual(approve_response.status_code, 200)

        report.refresh_from_db()

        self.assertEqual(report.status, SessionReport.Status.APPROVED)
        self.assertEqual(report.reviewed_by, self.education_officer)

        # monthly_summary
    def test_teacher_can_view_monthly_report_summary(self):
        second_session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 12, 10, 0)
            ),
            session_number=2,
        )

        third_session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 14, 10, 0)
            ),
            session_number=3,
        )

        fourth_session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 8, 16, 10, 0)
            ),
            session_number=4,
        )

        SessionReport.objects.create(
            session=self.session,
            lesson_summary="Report 1",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.PENDING,
            submitted_at=timezone.now(),
        )

        SessionReport.objects.create(
            session=second_session,
            lesson_summary="Report 2",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.APPROVED,
            submitted_at=timezone.now(),
        )

        SessionReport.objects.create(
            session=third_session,
            lesson_summary="Report 3",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.APPROVED,
            submitted_at=timezone.now(),
        )

        SessionReport.objects.create(
            session=fourth_session,
            lesson_summary="Report 4",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.REJECTED,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-monthly-summary")

        response = self.client.get(
            url,
            {
                "year": 2026,
                "month": 8,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["year"], 2026)
        self.assertEqual(response.data["month"], 8)
        self.assertEqual(response.data["pending"], 1)
        self.assertEqual(response.data["approved"], 2)
        self.assertEqual(response.data["rejected"], 1)
        self.assertEqual(response.data["total"], 4)


    def test_monthly_summary_only_counts_own_reports(self):
        other_teacher = User.objects.create_user(
            username="summary_other_teacher",
            first_name="Other",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07123456789",
            emergency_phone_number="07987654321",
        )

        other_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django",
            class_code="DJ109",
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

        SessionReport.objects.create(
            session=self.session,
            lesson_summary="Own report",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.PENDING,
            submitted_at=timezone.now(),
        )

        SessionReport.objects.create(
            session=other_session,
            lesson_summary="Other teacher report",
            present_count=8,
            absent_count=1,
            status=SessionReport.Status.APPROVED,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-monthly-summary")

        response = self.client.get(
            url,
            {
                "year": 2026,
                "month": 8,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pending"], 1)
        self.assertEqual(response.data["approved"], 0)
        self.assertEqual(response.data["rejected"], 0)
        self.assertEqual(response.data["total"], 1)


    def test_monthly_summary_only_counts_requested_month(self):
        september_session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 5, 10, 0)
            ),
            session_number=2,
        )

        SessionReport.objects.create(
            session=self.session,
            lesson_summary="August report",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.PENDING,
            submitted_at=timezone.now(),
        )

        SessionReport.objects.create(
            session=september_session,
            lesson_summary="September report",
            present_count=10,
            absent_count=2,
            status=SessionReport.Status.APPROVED,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-monthly-summary")

        response = self.client.get(
            url,
            {
                "year": 2026,
                "month": 8,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pending"], 1)
        self.assertEqual(response.data["approved"], 0)
        self.assertEqual(response.data["rejected"], 0)
        self.assertEqual(response.data["total"], 1)


    def test_monthly_summary_requires_year(self):
        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-monthly-summary")

        response = self.client.get(
            url,
            {
                "month": 8,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("year", response.data)


    def test_monthly_summary_requires_month(self):
        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-monthly-summary")

        response = self.client.get(
            url,
            {
                "year": 2026,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("month", response.data)


    def test_monthly_summary_rejects_invalid_month(self):
        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-monthly-summary")

        response = self.client.get(
            url,
            {
                "year": 2026,
                "month": 13,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("month", response.data)


    def test_monthly_summary_rejects_non_integer_year(self):
        self.client.force_authenticate(user=self.teacher)

        url = reverse("session-report-monthly-summary")

        response = self.client.get(
            url,
            {
                "year": "abc",
                "month": 8,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("year", response.data)


    def test_education_officer_cannot_view_monthly_summary(self):
        self.client.force_authenticate(user=self.education_officer)

        url = reverse("session-report-monthly-summary")

        response = self.client.get(
            url,
            {
                "year": 2026,
                "month": 8,
            },
        )

        self.assertEqual(response.status_code, 403)