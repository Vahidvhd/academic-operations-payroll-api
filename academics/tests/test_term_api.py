from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from academics.models import CourseClass, School, Term

User = get_user_model()

class TermAPITests(APITestCase):
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
        )

        self.finance_officer = User.objects.create_user(
            username="finance",
            first_name="Test",
            last_name="Finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.url = reverse("term-list")


    def test_education_officer_can_create_term(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "start_date": "2026-09-01",
                "end_date": "2026-12-31",
                "term_type": "regular",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Term.objects.filter(
                start_date="2026-09-01",
                end_date="2026-12-31",
                term_type="regular",
            ).exists()
        )

    def test_term_end_date_cannot_be_before_start_date(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "start_date": "2026-09-01",
                "end_date": "2026-08-31",
                "term_type": "regular",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.data)


    def test_term_start_date_must_be_first_day_of_month(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "start_date": "2026-09-15",
                "end_date": "2026-12-31",
                "term_type": "regular",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("start_date", response.data)


    def test_term_end_date_must_be_last_day_of_month(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "start_date": "2026-09-01",
                "end_date": "2026-12-20",
                "term_type": "regular",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.data)


    def test_term_dates_cannot_overlap_existing_term(self):
        Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-12-31",
            term_type="regular",
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "start_date": "2026-12-01",
                "end_date": "2027-03-31",
                "term_type": "regular",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("start_date", response.data)


    def test_empty_term_can_be_soft_deleted(self):
        term = Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-12-31",
            term_type="regular",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("term-detail", args=[term.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

        term.refresh_from_db()

        self.assertTrue(term.is_deleted)
        self.assertIsNotNone(term.deleted_at)


    def test_term_with_class_cannot_be_deleted(self):
        school = School.objects.create(
            name="Test School",
            address="London",
        )

        term = Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-12-31",
            term_type="regular",
        )

        CourseClass.objects.create(
            school=school,
            term=term,
            title="Python",
            class_code="PY101",
            start_date="2026-09-01",
            end_date="2026-12-31",
            session_duration=90,
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("term-detail", args=[term.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 400)

        term.refresh_from_db()

        self.assertFalse(term.is_deleted)
        self.assertIsNone(term.deleted_at)


    def test_term_cannot_be_updated_with_patch(self):
        term = Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-12-31",
            term_type="regular",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("term-detail", args=[term.id])

        response = self.client.patch(
            url,
            {
                "term_type": "summer",
            },
        )

        self.assertEqual(response.status_code, 405)


    def test_term_cannot_be_updated_with_put(self):
        term = Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-12-31",
            term_type="regular",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("term-detail", args=[term.id])

        response = self.client.put(
            url,
            {
                "start_date": "2026-09-01",
                "end_date": "2026-12-31",
                "term_type": "summer",
            },
        )

        self.assertEqual(response.status_code, 405)


    def test_education_officer_can_list_terms(self):
        Term.objects.create(
            start_date="2026-09-01",
            end_date="2026-12-31",
            term_type="regular",
        )

        self.client.force_authenticate(user=self.education_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026-09-01")


    def test_teacher_cannot_list_terms(self):
        self.client.force_authenticate(user=self.teacher)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)


    def test_finance_officer_cannot_list_terms(self):
        self.client.force_authenticate(user=self.finance_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)


    def test_anonymous_user_cannot_list_terms(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)