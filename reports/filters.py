from django_filters import rest_framework as filters

from reports.models import SessionReport


class SessionReportFilter(filters.FilterSet):
    school = filters.NumberFilter(field_name="session__course_class__school")
    course_class = filters.NumberFilter(field_name="session__course_class")
    teacher = filters.NumberFilter(field_name="session__course_class__teacher_assignments__teacher", distinct=True)
    date_from = filters.DateFilter(field_name="session__session_datetime", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="session__session_datetime", lookup_expr="date__lte")
    
    class Meta:
        model = SessionReport
        fields = [
            "school",
            "course_class",
            "teacher",
            "date_from",
            "date_to",
        ]