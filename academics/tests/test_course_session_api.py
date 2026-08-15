from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from academics.models import CourseClass, CourseSession, School, Term

User = get_user_model()


class CourseSessionAPITests(APITestCase):
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

        self.url = reverse("course-session-list")


    def test_education_officer_can_create_course_session(self):
        self.client.force_authenticate(user=self.education_officer)

        data = {
            "course_class": self.course_class.id,
            "session_datetime": "2026-09-10T10:00:00Z",
            "session_number": 1,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CourseSession.objects.count(), 1)

        session = CourseSession.objects.get()
        self.assertEqual(session.course_class, self.course_class)
        self.assertEqual(session.session_number, 1)


    def test_cannot_create_session_before_course_class_start_date(self):
        self.client.force_authenticate(user=self.education_officer)

        data = {
            "course_class": self.course_class.id,
            "session_datetime": "2026-08-31T10:00:00Z",
            "session_number": 1,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CourseSession.objects.count(), 0)


    def test_cannot_create_session_after_course_class_end_date(self):
        self.client.force_authenticate(user=self.education_officer)

        data = {
            "course_class": self.course_class.id,
            "session_datetime": "2027-01-01T10:00:00Z",
            "session_number": 1,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CourseSession.objects.count(), 0)


    def test_cannot_create_duplicate_session_number_for_same_course_class(self):
        self.client.force_authenticate(user=self.education_officer)

        CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime="2026-09-10T10:00:00Z",
            session_number=1,
        )

        data = {
            "course_class": self.course_class.id,
            "session_datetime": "2026-09-11T10:00:00Z",
            "session_number": 1,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(CourseSession.objects.count(), 1)