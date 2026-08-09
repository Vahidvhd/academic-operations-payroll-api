from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from academics.models import Term

User = get_user_model()

class TermAPITests(APITestCase):
    def setUp(self):
        self.education_officer = User.objects.create_user(
            username="education",
            first_name="Test",
            last_name="Education",
            role=User.Role.EDUCATION_OFFICER,
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