from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from users.permissions import (
    IsEducationOfficer,
    IsFinanceOfficer,
    IsTeacher,
)

User = get_user_model()

class TeacherOnlyView(APIView):
    permission_classes = [IsTeacher]

    def get(self, request):
        return Response({"message": "Teacher access granted."})


class EducationOfficerOnlyView(APIView):
    permission_classes = [IsEducationOfficer]

    def get(self, request):
        return Response({"message": "Education officer access granted."})


class FinanceOfficerOnlyView(APIView):
    permission_classes = [IsFinanceOfficer]

    def get(self, request):
        return Response({"message": "Finance officer access granted."})


class RolePermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.teacher = User.objects.create_user(
            username="teacher",
            first_name="Test",
            last_name="Teacher",
            role=User.Role.TEACHER,
            phone_number="07000000001",
            emergency_phone_number="07000000002",
        )

        self.education_officer = User.objects.create_user(
            username="education",
            first_name="Test",
            last_name="Education",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.finance_officer = User.objects.create_user(
            username="finance",
            first_name="Test",
            last_name="Finance",
            role=User.Role.FINANCE_OFFICER,
        )

    def send_request(self, view_class, user=None):
        request = self.factory.get("/")
        if user is not None:
            force_authenticate(request, user=user)
        view = view_class.as_view()
        return view(request)


    def test_teacher_can_access_teacher_view(self):
        response = self.send_request(TeacherOnlyView, self.teacher)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_education_officer_cannot_access_teacher_view(self):
        response = self.send_request(TeacherOnlyView, self.education_officer)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_finance_officer_cannot_access_teacher_view(self):
        response = self.send_request(TeacherOnlyView, self.finance_officer)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_unauthenticated_user_cannot_access_teacher_view(self):
        response = self.send_request(TeacherOnlyView)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_education_officer_can_access_education_view(self):
        response = self.send_request(EducationOfficerOnlyView, self.education_officer)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_teacher_cannot_access_education_view(self):
        response = self.send_request(EducationOfficerOnlyView, self.teacher)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_finance_officer_cannot_access_education_view(self):
        response = self.send_request(EducationOfficerOnlyView, self.finance_officer)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_unauthenticated_user_cannot_access_education_view(self):
        response = self.send_request(EducationOfficerOnlyView)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_finance_officer_can_access_finance_view(self):
        response = self.send_request(FinanceOfficerOnlyView, self.finance_officer)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_teacher_cannot_access_finance_view(self):
        response = self.send_request(FinanceOfficerOnlyView, self.teacher)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_education_officer_cannot_access_finance_view(self):
        response = self.send_request(FinanceOfficerOnlyView, self.education_officer)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_unauthenticated_user_cannot_access_finance_view(self):
        response = self.send_request(FinanceOfficerOnlyView)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)