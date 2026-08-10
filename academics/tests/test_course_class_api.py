from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from academics.models import CourseClass, School, Term

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