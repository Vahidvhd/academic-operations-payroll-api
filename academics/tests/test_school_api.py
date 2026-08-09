from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from academics.models import School

User = get_user_model()


class SchoolAPITests(APITestCase):
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

        self.finance_officer = User.objects.create_user(
            username="finance",
            first_name="Test",
            last_name="Finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.url = reverse("school-list")

    def test_education_officer_can_list_schools(self):
        School.objects.create(name="Test School", address="London")

        self.client.force_authenticate(user=self.education_officer)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test School")


    def test_education_officer_can_create_school(self):
        self.client.force_authenticate(user=self.education_officer)

        response = self.client.post(
            self.url,
            {
                "name": "New School",
                "address": "London",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(School.objects.filter(name="New School", address="London").exists())


    def test_teacher_cannot_create_school(self):
        self.client.force_authenticate(user=self.teacher)

        response = self.client.post(
            self.url,
            {
                "name": "Blocked School",
                "address": "London",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(School.objects.filter(name="Blocked School", address="London").exists())


    def test_teacher_cannot_list_schools(self):
        self.client.force_authenticate(user=self.teacher)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)


    def test_finance_officer_cannot_list_schools(self):
        self.client.force_authenticate(user=self.finance_officer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)


    def test_education_officer_can_update_school(self):
        school = School.objects.create(name="Old School", address="Old Address")

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("school-detail", args=[school.id])

        response = self.client.patch(
            url,
            {
                "name": "Updated School",
            },
        )

        self.assertEqual(response.status_code, 200)

        school.refresh_from_db()

        self.assertEqual(school.name, "Updated School")
        self.assertEqual(school.address, "Old Address")


    def test_education_officer_can_soft_delete_school(self):
        school = School.objects.create(
            name="Delete School",
            address="London",
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("school-detail", args=[school.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

        school.refresh_from_db()

        self.assertTrue(school.is_deleted)
        self.assertIsNotNone(school.deleted_at)

        list_response = self.client.get(self.url)

        self.assertEqual(list_response.status_code, 200)
        self.assertNotContains(list_response, "Delete School")


    def test_soft_deleted_school_detail_returns_404(self):
        school = School.objects.create(
            name="Deleted School",
            address="London",
            is_deleted=True,
        )

        self.client.force_authenticate(user=self.education_officer)

        url = reverse("school-detail", args=[school.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


    def test_anonymous_user_cannot_list_schools(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
