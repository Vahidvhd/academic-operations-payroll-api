from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission, SAFE_METHODS


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


class IsEducationOfficerOrTeacher(BasePermission):
    message = "User does not have permission."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == User.Role.EDUCATION_OFFICER:
            return True

        return (
            request.user.role == User.Role.TEACHER
            and request.method in SAFE_METHODS
        )


class IsSuperUser(BasePermission):
    message = "Only superusers have permission."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_superuser
        )


class IsFinanceOfficerOrTeacher(BasePermission):
    message = "User does not have permission."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == User.Role.FINANCE_OFFICER:
            return True

        return (
            request.user.role == User.Role.TEACHER
            and request.method in SAFE_METHODS
        )