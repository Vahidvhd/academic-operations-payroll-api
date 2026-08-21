from django.urls import path

from users.views import (
    AdminUserCreateView,
    CurrentUserView,
)

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("admin/create/", AdminUserCreateView.as_view(), name="admin-user-create"),
]