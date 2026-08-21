from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AdminUserCreateAPITests(APITestCase):
    def test_superuser_can_create_teacher(self):
        superuser = User.objects.create_superuser(
            username="admin",
            password="Admin123!",
            first_name="Admin",
            last_name="User",
        )

        self.client.force_authenticate(user=superuser)

        url = reverse("admin-user-create")

        response = self.client.post(
            url,
            {
                "username": "new_teacher",
                "password": "Teacher123!",
                "first_name": "New",
                "last_name": "Teacher",
                "role": User.Role.TEACHER,
                "phone_number": "07111111111",
                "emergency_phone_number": "07222222222",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = User.objects.get(username="new_teacher")

        self.assertEqual(user.role, User.Role.TEACHER)
        self.assertEqual(user.phone_number, "07111111111")
        self.assertEqual(
            user.emergency_phone_number,
            "07222222222",
        )

        self.assertTrue(
            user.check_password("Teacher123!")
        )

        self.assertNotIn("password", response.data)


    def test_superuser_cannot_create_teacher_without_phone_numbers(self):
        superuser = User.objects.create_superuser(
            username="admin2",
            password="Admin123!",
            first_name="Admin",
            last_name="User",
        )

        self.client.force_authenticate(user=superuser)

        url = reverse("admin-user-create")

        response = self.client.post(
            url,
            {
                "username": "teacher_without_phone",
                "password": "Teacher123!",
                "first_name": "No",
                "last_name": "Phone",
                "role": User.Role.TEACHER,
                "phone_number": "",
                "emergency_phone_number": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("phone_number", response.data)


    def test_superuser_can_create_education_officer_without_phone_numbers(self):
        superuser = User.objects.create_superuser(
            username="admin3",
            password="Admin123!",
            first_name="Admin",
            last_name="User",
        )

        self.client.force_authenticate(user=superuser)

        url = reverse("admin-user-create")

        response = self.client.post(
            url,
            {
                "username": "new_education",
                "password": "Education123!",
                "first_name": "New",
                "last_name": "Education",
                "role": User.Role.EDUCATION_OFFICER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        user = User.objects.get(username="new_education")
        self.assertEqual(
            user.role,
            User.Role.EDUCATION_OFFICER,
        )