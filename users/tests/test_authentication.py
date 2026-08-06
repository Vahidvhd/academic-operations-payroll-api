from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.password = "Test123@"
        self.user = User.objects.create_user(
            username="teacher1",
            password=self.password,
            first_name="Teacher",
            last_name="One",
            role=User.Role.TEACHER,
        )

    def test_user_can_obtain_jwt_tokens(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(
            url,
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_unauthenticated_user_cannot_access_current_user(self):
        url = reverse("current-user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_access_current_user(self):
        token_url = reverse("token_obtain_pair")

        token_response = self.client.post(
            token_url,
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )
        access_token = token_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        current_user_url = reverse("current-user")
        response = self.client.get(current_user_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["role"], User.Role.TEACHER)
        self.assertEqual(response.data["first_name"], self.user.first_name)
        self.assertEqual(response.data["last_name"], self.user.last_name)

    def test_user_can_refresh_access_token(self):
        token_url = reverse("token_obtain_pair")

        token_response = self.client.post(
            token_url,
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )

        refresh_token = token_response.data["refresh"]
        refresh_url = reverse("token_refresh")
        response = self.client.post(
            refresh_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_user_cannot_obtain_tokens_with_wrong_password(self):
        url = reverse("token_obtain_pair")

        response = self.client.post(
            url,
            {
                "username": self.user.username,
                "password": "WrongPassword",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)