from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from academics.models import CourseClass, School, Term, TeacherClassAssignment

User = get_user_model()


class CourseClassAPITests(APITestCase):
    def setUp(self):
        self.education_officer = User.objects.create_user(
            username="education",
            first_name="Test",
            last_name="Education",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.school = School.objects.create(
            name="Test School",
            address="London",
        )

        self.term = Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-12-31",
            term_type="regular",
        )

        self.teacher = User.objects.create_user(
            username="teacher",
            first_name="Test",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07111111111",
            emergency_phone_number="07222222222",
        )


        self.finance_officer = User.objects.create_user(
            username="finance",
            first_name="Test",
            last_name="Finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.url = reverse("course-class-list")

    def test_education_officer_can_create_course_class(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": self.school.id,
                "term": self.term.id,
                "title": "Python",
                "class_code": "PY101",
                "start_date": "2026-09-01",
                "end_date": "2026-12-31",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            CourseClass.objects.filter(
                school=self.school,
                term=self.term,
                class_code="PY101",
            ).exists()
        )

    def test_course_class_end_date_cannot_be_before_start_date(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": self.school.id,
                "term": self.term.id,
                "title": "Python",
                "class_code": "PY102",
                "start_date": "2026-10-01",
                "end_date": "2026-09-30",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.data)


    def test_course_class_cannot_start_before_term(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": self.school.id,
                "term": self.term.id,
                "title": "Python",
                "class_code": "PY103",
                "start_date": "2026-08-31",
                "end_date": "2026-12-31",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("start_date", response.data)


    def test_course_class_cannot_end_after_term(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": self.school.id,
                "term": self.term.id,
                "title": "Python",
                "class_code": "PY104",
                "start_date": "2026-09-01",
                "end_date": "2027-01-01",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.data)


    def test_course_class_rejects_invalid_session_duration(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": self.school.id,
                "term": self.term.id,
                "title": "Python",
                "class_code": "PY105",
                "start_date": "2026-09-01",
                "end_date": "2026-12-31",
                "session_duration": 45,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("session_duration", response.data)


    def test_course_class_code_must_be_unique_per_school_and_term(self):
        CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY106",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": self.school.id,
                "term": self.term.id,
                "title": "Python Advanced",
                "class_code": "PY106",
                "start_date": "2026-09-01",
                "end_date": "2026-12-31",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_education_officer_can_partially_update_course_class(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY107",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("course-class-detail", args=[course_class.id])

        response = self.client.patch(
            url,
            {
                "title": "Python Advanced",
            },
        )

        self.assertEqual(response.status_code, 200)

        course_class.refresh_from_db()

        self.assertEqual(course_class.title, "Python Advanced")


    def test_partial_update_rejects_invalid_course_class_dates(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY108",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("course-class-detail", args=[course_class.id])

        response = self.client.patch(
            url,
            {
                "start_date": "2027-01-01",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.data)


    def test_education_officer_can_soft_delete_course_class(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY109",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("course-class-detail", args=[course_class.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

        course_class.refresh_from_db()

        self.assertTrue(course_class.is_deleted)
        self.assertIsNotNone(course_class.deleted_at)


    def test_soft_deleted_course_class_is_not_in_list(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY110",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
            is_deleted=True,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data]

        self.assertNotIn(course_class.id, returned_ids)


    def test_soft_deleted_course_class_detail_returns_404(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY111",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
            is_deleted=True,
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("course-class-detail", args=[course_class.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_teacher_can_list_only_assigned_course_classes(self):
        assigned_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Assigned Class",
            class_code="PY118",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        unassigned_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Unassigned Class",
            class_code="PY119",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=assigned_class,
            start_date="2026-09-01",
            end_date="2026-12-31",
        )

        self.client.force_authenticate(user=self.teacher)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data]

        self.assertIn(assigned_class.id, returned_ids)
        self.assertNotIn(unassigned_class.id, returned_ids)

    def test_teacher_can_retrieve_assigned_course_class(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Assigned Class",
            class_code="PY120",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=course_class,
            start_date="2026-09-01",
            end_date="2026-12-31",
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("course-class-detail", args=[course_class.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], course_class.id)


    def test_teacher_cannot_retrieve_unassigned_course_class(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Unassigned Class",
            class_code="PY121",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("course-class-detail", args=[course_class.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


    def test_teacher_cannot_create_course_class(self):
        self.client.force_authenticate(user=self.teacher)

        response = self.client.post(
            self.url,
            {
                "school": self.school.id,
                "term": self.term.id,
                "title": "Python",
                "class_code": "PY122",
                "start_date": "2026-09-01",
                "end_date": "2026-12-31",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 403)


    def test_teacher_cannot_update_assigned_course_class(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Assigned Class",
            class_code="PY123",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=course_class,
            start_date="2026-09-01",
            end_date="2026-12-31",
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("course-class-detail", args=[course_class.id])

        response = self.client.patch(
            url,
            {
                "title": "Changed Title",
            },
        )

        self.assertEqual(response.status_code, 403)


    def test_teacher_cannot_delete_assigned_course_class(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Assigned Class",
            class_code="PY124",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=course_class,
            start_date="2026-09-01",
            end_date="2026-12-31",
        )

        self.client.force_authenticate(user=self.teacher)

        url = reverse("course-class-detail", args=[course_class.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)


    def test_finance_officer_cannot_list_course_classes(self):
        self.client.force_authenticate(user=self.finance_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)


    def test_anonymous_user_cannot_list_course_classes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)


    def test_education_officer_can_list_course_classes(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY112",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data]

        self.assertIn(course_class.id, returned_ids)


    def test_education_officer_can_retrieve_course_class(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY113",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("course-class-detail", args=[course_class.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], course_class.id)


    def test_same_class_code_is_allowed_for_different_school(self):
        other_school = School.objects.create(
            name="Other School",
            address="Manchester",
        )

        CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY114",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": other_school.id,
                "term": self.term.id,
                "title": "Python Advanced",
                "class_code": "PY114",
                "start_date": "2026-09-01",
                "end_date": "2026-12-31",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 201)


    def test_same_class_code_is_allowed_for_different_term(self):
        other_term = Term.objects.create(
            start_date="2027-01-01",
            end_date="2027-03-31",
            term_type="regular",
        )

        CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY115",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": self.school.id,
                "term": other_term.id,
                "title": "Python Advanced",
                "class_code": "PY115",
                "start_date": "2027-01-01",
                "end_date": "2027-03-31",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 201)


    def test_course_class_cannot_use_soft_deleted_school(self):
        deleted_school = School.objects.create(
            name="Deleted School",
            address="London",
            is_deleted=True,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": deleted_school.id,
                "term": self.term.id,
                "title": "Python",
                "class_code": "PY116",
                "start_date": "2026-09-01",
                "end_date": "2026-12-31",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("school", response.data)


    def test_course_class_cannot_use_soft_deleted_term(self):
        deleted_term = Term.objects.create(
            start_date="2027-01-01",
            end_date="2027-03-31",
            term_type="regular",
            is_deleted=True,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "school": self.school.id,
                "term": deleted_term.id,
                "title": "Python",
                "class_code": "PY117",
                "start_date": "2027-01-01",
                "end_date": "2027-03-31",
                "session_duration": 90,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("term", response.data)


    # Filtering

    def test_course_classes_can_be_filtered_by_school(self):
        other_school = School.objects.create(
            name="Other School",
            address="Manchester",
        )

        class_in_first_school = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="PY201",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        class_in_other_school = CourseClass.objects.create(
            school=other_school,
            term=self.term,
            title="Django",
            class_code="DJ201",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {"school": self.school.id},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data]

        self.assertIn(class_in_first_school.id, returned_ids)
        self.assertNotIn(class_in_other_school.id, returned_ids)


    def test_course_classes_can_be_filtered_by_term(self):
        other_term = Term.objects.create(
            start_date="2027-01-01",
            end_date="2027-03-31",
            term_type="regular",
        )

        class_in_first_term = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="PY202",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        class_in_other_term = CourseClass.objects.create(
            school=self.school,
            term=other_term,
            title="Django",
            class_code="DJ202",
            start_date="2027-01-01",
            end_date="2027-03-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {"term": self.term.id},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data]

        self.assertIn(class_in_first_term.id, returned_ids)
        self.assertNotIn(class_in_other_term.id, returned_ids)


    def test_course_classes_can_be_filtered_by_teacher(self):
        other_teacher = User.objects.create_user(
            username="other_teacher",
            first_name="Other",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07333333333",
            emergency_phone_number="07444444444",
        )

        first_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="PY203",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        second_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django",
            class_code="DJ203",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=first_class,
            start_date="2026-09-01",
            end_date="2026-12-31",
        )

        TeacherClassAssignment.objects.create(
            teacher=other_teacher,
            course_class=second_class,
            start_date="2026-09-01",
            end_date="2026-12-31",
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(
            self.url,
            {"teacher": self.teacher.id},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data]

        self.assertIn(first_class.id, returned_ids)
        self.assertNotIn(second_class.id, returned_ids)


    def test_teacher_filter_cannot_expose_other_teachers_classes(self):
        other_teacher = User.objects.create_user(
            username="filter_other_teacher",
            first_name="Other",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07555555555",
            emergency_phone_number="07666666666",
        )

        own_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Own Class",
            class_code="PY204",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        other_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Other Class",
            class_code="DJ204",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=own_class,
            start_date="2026-09-01",
            end_date="2026-12-31",
        )

        TeacherClassAssignment.objects.create(
            teacher=other_teacher,
            course_class=other_class,
            start_date="2026-09-01",
            end_date="2026-12-31",
        )

        self.client.force_authenticate(user=self.teacher)

        response = self.client.get(
            self.url,
            {"teacher": other_teacher.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])