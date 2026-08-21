from django.contrib import admin

from reports.models import ReportStatusHistory, SessionReport


@admin.register(SessionReport)
class SessionReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "status",
        "submitted_at",
        "late_hours",
        "reviewed_by",
        "created_at",
    )

    search_fields = (
        "session__course_class__title",
        "session__course_class__class_code",
        "lesson_summary",
        "reviewed_by__username",
    )

    list_filter = (
        "status",
        "session__course_class__school",
        "session__course_class",
    )

    ordering = (
        "-submitted_at",
    )

    readonly_fields = (
        "session",
        "lesson_summary",
        "present_count",
        "absent_count",
        "status",
        "submitted_at",
        "late_hours",
        "reviewed_by",
        "review_note",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReportStatusHistory)
class ReportStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session_report",
        "old_status",
        "new_status",
        "changed_by",
        "created_at",
    )

    search_fields = (
        "session_report__id",
        "changed_by__username",
        "changed_by__first_name",
        "changed_by__last_name",
        "note",
    )

    list_filter = (
        "old_status",
        "new_status",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "session_report",
        "old_status",
        "new_status",
        "changed_by",
        "note",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False