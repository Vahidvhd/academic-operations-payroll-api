from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission


User = get_user_model()


class IsTeacher(BasePermission):
    message = "User does not have permission."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.TEACHER
        )


class IsEducationOfficer(BasePermission):
    message = "User does not have permission."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.EDUCATION_OFFICER
        )


class IsFinanceOfficer(BasePermission):
    message = "User does not have permission."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.FINANCE_OFFICER
        )