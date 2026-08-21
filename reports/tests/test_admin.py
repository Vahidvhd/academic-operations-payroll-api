from django.contrib import admin
from django.test import TestCase

from reports.admin import (
    ReportStatusHistoryAdmin,
    SessionReportAdmin,
)
from reports.models import (
    ReportStatusHistory,
    SessionReport,
)


class ReportsAdminTests(TestCase):
    def test_session_report_admin_disables_add_and_delete(self):
        model_admin = SessionReportAdmin(
            SessionReport,
            admin.site,
        )

        self.assertFalse(
            model_admin.has_add_permission(None)
        )

        self.assertFalse(
            model_admin.has_delete_permission(None)
        )

    def test_report_status_history_admin_disables_add_and_delete(self):
        model_admin = ReportStatusHistoryAdmin(
            ReportStatusHistory,
            admin.site,
        )

        self.assertFalse(
            model_admin.has_add_permission(None)
        )

        self.assertFalse(
            model_admin.has_delete_permission(None)
        )