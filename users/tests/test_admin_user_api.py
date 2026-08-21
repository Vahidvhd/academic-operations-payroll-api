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


    def test_teacher_cannot_create_user_via_admin_api(self):
        teacher = User.objects.create_user(
            username="teacher_user",
            password="Teacher123!",
            first_name="Test",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07111111111",
            emergency_phone_number="07222222222",
        )

        self.client.force_authenticate(user=teacher)

        url = reverse("admin-user-create")

        response = self.client.post(
            url,
            {
                "username": "new_user",
                "password": "User123!",
                "first_name": "New",
                "last_name": "User",
                "role": User.Role.EDUCATION_OFFICER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            User.objects.filter(username="new_user").exists()
        )


    def test_education_officer_cannot_create_user_via_admin_api(self):
        education_officer = User.objects.create_user(
            username="education_user",
            password="Education123!",
            first_name="Test",
            last_name="Education",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.client.force_authenticate(user=education_officer)

        url = reverse("admin-user-create")

        response = self.client.post(
            url,
            {
                "username": "new_user",
                "password": "User123!",
                "first_name": "New",
                "last_name": "User",
                "role": User.Role.FINANCE_OFFICER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            User.objects.filter(username="new_user").exists()
        )


    def test_finance_officer_cannot_create_user_via_admin_api(self):
        finance_officer = User.objects.create_user(
            username="finance_user",
            password="Finance123!",
            first_name="Test",
            last_name="Finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.client.force_authenticate(user=finance_officer)

        url = reverse("admin-user-create")

        response = self.client.post(
            url,
            {
                "username": "new_user",
                "password": "User123!",
                "first_name": "New",
                "last_name": "User",
                "role": User.Role.TEACHER,
                "phone_number": "07111111111",
                "emergency_phone_number": "07222222222",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            User.objects.filter(username="new_user").exists()
        )


    def test_anonymous_user_cannot_create_user_via_admin_api(self):
        url = reverse("admin-user-create")

        response = self.client.post(
            url,
            {
                "username": "new_user",
                "password": "User123!",
                "first_name": "New",
                "last_name": "User",
                "role": User.Role.EDUCATION_OFFICER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(
            User.objects.filter(username="new_user").exists()
        )


    def test_superuser_cannot_create_user_with_weak_password(self):
        superuser = User.objects.create_superuser(
            username="admin4",
            password="Admin123!",
            first_name="Admin",
            last_name="User",
        )

        self.client.force_authenticate(user=superuser)

        url = reverse("admin-user-create")

        response = self.client.post(
            url,
            {
                "username": "weak_password_user",
                "password": "123",
                "first_name": "Weak",
                "last_name": "Password",
                "role": User.Role.EDUCATION_OFFICER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)

        self.assertFalse(
            User.objects.filter(
                username="weak_password_user"
            ).exists()
        )