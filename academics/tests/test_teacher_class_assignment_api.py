from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from academics.models import CourseClass, School, TeacherClassAssignment, Term

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
        self.assertIn("teacher", response.data)


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
        self.assertIn("teacher", response.data)


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
        self.assertIn("course_class", response.data)


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
        self.assertIn("start_date", response.data)


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
        self.assertIn("end_date", response.data)


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
        self.assertIn("start_date", response.data)


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
        self.assertIn("start_date", response.data)


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
        self.assertIn("start_date", response.data)


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