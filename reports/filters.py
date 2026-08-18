from django_filters import rest_framework as filters

from reports.models import SessionReport


class SessionReportFilter(filters.FilterSet):
    school = filters.NumberFilter(field_name="session__course_class__school")
    course_class = filters.NumberFilter(field_name="session__course_class")
    teacher = filters.NumberFilter(field_name="session__course_class__teacher_assignments__teacher", distinct=True)

    class Meta:
        model = SessionReport
        fields = [
            "school",
            "course_class",
            "teacher",
        ]