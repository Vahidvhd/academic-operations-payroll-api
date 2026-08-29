from django.contrib import admin
from django.test import RequestFactory, TestCase

from academics.admin import SoftDeleteAdmin
from academics.models import School


class SoftDeleteAdminTests(TestCase):
    def test_queryset_includes_deleted_records_and_applies_ordering(self):
        active_school = School.objects.create(
            name="Beta School",
            address="Active Address",
        )
        deleted_school = School.objects.create(
            name="Alpha School",
            address="Deleted Address",
        )
        deleted_school.delete()

        model_admin = SoftDeleteAdmin(School, admin.site)
        model_admin.ordering = ("name",)
        request = RequestFactory().get("/admin/academics/school/")

        queryset = model_admin.get_queryset(request)

        self.assertQuerySetEqual(
            queryset,
            [deleted_school, active_school],
        )