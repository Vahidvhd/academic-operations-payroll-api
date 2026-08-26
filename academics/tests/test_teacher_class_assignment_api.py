from datetime import datetime

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


class TeacherClassAssignmentAPITests(APITestCase):
    def setUp(self):
        self.education_officer = User.objects.create_user(
            username="education",
            first_name="Test",
            last_name="Education",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.teacher = User.objects.create_user(
            username="teacher",
            first_name="Test",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07111111111",
            emergency_phone_number="07222222222",
        )

        self.school = School.objects.create(
            name="Test School",
            address="London",
        )

        self.term = Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-12-31",
            term_type=Term.TermType.REGULAR,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="PY101",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.url = reverse("teacher-class-assignment-list")


    def test_education_officer_can_create_teacher_class_assignment(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": self.teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-09-01",
                "end_date": "2026-10-31",
            },
        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(TeacherClassAssignment.objects.filter(teacher=self.teacher,course_class=self.course_class).exists())


    def test_cannot_assign_non_teacher_user(self):
        finance_officer = User.objects.create_user(
            username="finance",
            first_name="Test",
            last_name="Finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": finance_officer.id,
                "course_class": self.course_class.id,
                "start_date": "2026-09-01",
                "end_date": "2026-10-31",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "teacher",
            response.data["error_message"],
        )

    def test_cannot_assign_inactive_teacher(self):
        inactive_teacher = User.objects.create_user(
            username="inactive_teacher",
            first_name="Inactive",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07333333333",
            emergency_phone_number="07444444444",
            is_active=False,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": inactive_teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-09-01",
                "end_date": "2026-10-31",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "teacher",
            response.data["error_message"],
        )

    def test_cannot_assign_teacher_to_soft_deleted_course_class(self):
        deleted_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Deleted Class",
            class_code="PY102",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
            is_deleted=True,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": self.teacher.id,
                "course_class": deleted_course_class.id,
                "start_date": "2026-09-01",
                "end_date": "2026-10-31",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "course_class",
            response.data["error_message"],
        )

    def test_assignment_cannot_start_before_course_class(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": self.teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-08-31",
                "end_date": "2026-10-31",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "start_date",
            response.data["error_message"],
        )

    def test_assignment_cannot_end_after_course_class(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": self.teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-09-01",
                "end_date": "2027-01-01",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "end_date",
            response.data["error_message"],
        )

    def test_assignments_for_same_course_class_cannot_overlap(self):
        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-10-15",
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07555555555",
            emergency_phone_number="07666666666",
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": second_teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-10-01",
                "end_date": "2026-11-30",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "start_date",
            response.data["error_message"],
        )

    def test_open_assignment_cannot_overlap_new_assignment(self):
        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date=None,
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07555555555",
            emergency_phone_number="07666666666",
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": second_teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-10-01",
                "end_date": "2026-11-30",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "start_date",
            response.data["error_message"],
        )

    def test_sequential_assignments_are_allowed(self):
        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-10-15",
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07555555555",
            emergency_phone_number="07666666666",
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": second_teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-10-16",
                "end_date": "2026-11-30",
            },
        )

        self.assertEqual(response.status_code, 201)


    def test_education_officer_can_update_assignment_end_date(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-10-15",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("teacher-class-assignment-detail", args=[assignment.id])

        response = self.client.patch(
            url,
            {
                "end_date": "2026-10-31",
            },
        )

        self.assertEqual(response.status_code, 200)

        assignment.refresh_from_db()

        self.assertEqual(str(assignment.end_date),"2026-10-31")


    def test_updating_assignment_cannot_create_overlap(self):
        first_assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-10-15",
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07555555555",
            emergency_phone_number="07666666666",
        )

        TeacherClassAssignment.objects.create(
            teacher=second_teacher,
            course_class=self.course_class,
            start_date="2026-10-16",
            end_date="2026-11-30",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse(
            "teacher-class-assignment-detail",
            args=[first_assignment.id],
        )

        response = self.client.patch(
            url,
            {
                "end_date": "2026-10-20",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "start_date",
            response.data["error_message"],
        )


    def test_teacher_cannot_list_teacher_class_assignments(self):
        self.client.force_authenticate(user=self.teacher)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)


    def test_finance_officer_cannot_list_teacher_class_assignments(self):
        finance_officer = User.objects.create_user(
            username="finance",
            first_name="Test",
            last_name="Finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.client.force_authenticate(user=finance_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)


    def test_anonymous_user_cannot_list_teacher_class_assignments(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)


    def test_education_officer_can_list_teacher_class_assignments(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-10-31",
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data]

        self.assertIn(assignment.id, returned_ids)


    def test_education_officer_can_retrieve_teacher_class_assignment(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-10-31",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse(
            "teacher-class-assignment-detail",
            args=[assignment.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], assignment.id)


    def test_assignment_can_have_no_end_date(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": self.teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-09-01",
                "end_date": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["end_date"])


    def test_assignments_cannot_share_same_boundary_date(self):
        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-10-15",
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07555555555",
            emergency_phone_number="07666666666",
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": second_teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-10-15",
                "end_date": "2026-11-30",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "start_date",
            response.data["error_message"],
        )

    def test_assignment_end_date_cannot_be_before_start_date(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": self.teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2026-10-15",
                "end_date": "2026-10-01",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "end_date",
            response.data["error_message"],
        )

    def test_assignment_cannot_start_after_course_class_ends(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "teacher": self.teacher.id,
                "course_class": self.course_class.id,
                "start_date": "2027-01-01",
                "end_date": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "start_date",
            response.data["error_message"],
        )

    def test_cannot_change_teacher_when_assignment_has_reported_session(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-09-30",
        )

        session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 10, 10, 0)
            ),
            session_number=1,
        )

        SessionReport.objects.create(
            session=session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07555555555",
            emergency_phone_number="07666666666",
        )

        self.client.force_authenticate(
            user=self.education_officer,
        )

        url = reverse(
            "teacher-class-assignment-detail",
            args=[assignment.id],
        )

        response = self.client.patch(
            url,
            {
                "teacher": second_teacher.id,
            },
        )

        self.assertEqual(response.status_code, 400)

        assignment.refresh_from_db()

        self.assertEqual(assignment.teacher, self.teacher)


    def test_cannot_shorten_assignment_past_reported_session(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-09-30",
        )

        session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 12, 10, 0)
            ),
            session_number=1,
        )

        SessionReport.objects.create(
            session=session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(
            user=self.education_officer,
        )

        url = reverse(
            "teacher-class-assignment-detail",
            args=[assignment.id],
        )

        response = self.client.patch(
            url,
            {
                "end_date": "2026-09-10",
            },
        )

        self.assertEqual(response.status_code, 400)

        assignment.refresh_from_db()

        self.assertEqual(str(assignment.end_date), "2026-09-30")


    def test_cannot_delete_assignment_with_reported_session(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-09-30",
        )

        session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 10, 10, 0)
            ),
            session_number=1,
        )

        SessionReport.objects.create(
            session=session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(
            user=self.education_officer,
        )

        url = reverse(
            "teacher-class-assignment-detail",
            args=[assignment.id],
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 400)

        self.assertTrue(
            TeacherClassAssignment.objects.filter(
                id=assignment.id,
            ).exists()
        )


    def test_cannot_change_course_class_of_existing_assignment(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-09-30",
        )

        second_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django",
            class_code="DJ101",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(
            user=self.education_officer,
        )

        url = reverse(
            "teacher-class-assignment-detail",
            args=[assignment.id],
        )

        response = self.client.patch(
            url,
            {
                "course_class": second_course_class.id,
            },
        )

        self.assertEqual(response.status_code, 400)

        assignment.refresh_from_db()

        self.assertEqual(
            assignment.course_class,
            self.course_class,
        )


    def test_can_shorten_assignment_if_reported_sessions_stay_in_range(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-09-30",
        )

        session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 5, 10, 0)
            ),
            session_number=1,
        )

        SessionReport.objects.create(
            session=session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(
            user=self.education_officer,
        )

        url = reverse(
            "teacher-class-assignment-detail",
            args=[assignment.id],
        )

        response = self.client.patch(
            url,
            {
                "end_date": "2026-09-10",
            },
        )

        self.assertEqual(response.status_code, 200)

        assignment.refresh_from_db()

        self.assertEqual(str(assignment.end_date), "2026-09-10")


    def test_cannot_move_assignment_start_date_past_reported_session(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-09-30",
        )

        session = CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 9, 10, 10, 0)
            ),
            session_number=1,
        )

        SessionReport.objects.create(
            session=session,
            lesson_summary="Python basics",
            present_count=10,
            absent_count=2,
            submitted_at=timezone.now(),
        )

        self.client.force_authenticate(
            user=self.education_officer,
        )

        url = reverse(
            "teacher-class-assignment-detail",
            args=[assignment.id],
        )

        response = self.client.patch(
            url,
            {
                "start_date": "2026-09-12",
            },
        )

        self.assertEqual(response.status_code, 400)

        assignment.refresh_from_db()

        self.assertEqual(
            str(assignment.start_date),
            "2026-09-01",
        )


    def test_can_delete_assignment_without_reported_sessions(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date="2026-09-01",
            end_date="2026-09-30",
        )

        self.client.force_authenticate(
            user=self.education_officer,
        )

        url = reverse(
            "teacher-class-assignment-detail",
            args=[assignment.id],
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

        self.assertFalse(
            TeacherClassAssignment.objects.filter(
                id=assignment.id
            ).exists()
        )