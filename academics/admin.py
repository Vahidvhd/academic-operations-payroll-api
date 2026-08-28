from django.contrib import admin

from academics.models import (
    CourseClass,
    CourseSession,
    School,
    TeacherClassAssignment,
    Term,
)


class SoftDeleteAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        queryset = self.model.all_objects.all()

        ordering = self.get_ordering(request)
        if ordering:
            queryset = queryset.order_by(*ordering)

        return queryset

    
@admin.register(School)
class SchoolAdmin(SoftDeleteAdmin):
    list_display = (
        "id",
        "name",
        "address",
        "is_deleted",
        "created_at",
    )

    search_fields = (
        "name",
        "address",
    )

    list_filter = (
        "is_deleted",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )


@admin.register(Term)
class TermAdmin(SoftDeleteAdmin):
    list_display = (
        "id",
        "term_type",
        "start_date",
        "end_date",
        "is_deleted",
        "created_at",
    )

    list_filter = (
        "term_type",
        "is_deleted",
    )

    ordering = (
        "-start_date",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )


@admin.register(CourseClass)
class CourseClassAdmin(SoftDeleteAdmin):
    list_display = (
        "id",
        "title",
        "class_code",
        "school",
        "term",
        "start_date",
        "end_date",
        "session_duration",
        "is_deleted",
    )

    search_fields = (
        "title",
        "class_code",
        "school__name",
    )

    list_filter = (
        "school",
        "term",
        "session_duration",
        "is_deleted",
    )

    ordering = (
        "-start_date",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )


@admin.register(TeacherClassAssignment)
class TeacherClassAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "teacher",
        "course_class",
        "start_date",
        "end_date",
        "created_at",
    )

    search_fields = (
        "teacher__username",
        "teacher__first_name",
        "teacher__last_name",
        "course_class__title",
        "course_class__class_code",
    )

    list_filter = (
        "course_class",
        "start_date",
        "end_date",
    )

    ordering = (
        "-start_date",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(CourseSession)
class CourseSessionAdmin(SoftDeleteAdmin):
    list_display = (
        "id",
        "course_class",
        "session_number",
        "session_datetime",
        "is_deleted",
        "created_at",
    )

    search_fields = (
        "course_class__title",
        "course_class__class_code",
    )

    list_filter = (
        "course_class",
        "is_deleted",
    )

    ordering = (
        "-session_datetime",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )