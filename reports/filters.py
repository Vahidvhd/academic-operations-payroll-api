from django_filters import rest_framework as filters

from academics.models import CourseSession
from academics.services import filter_sessions_for_teacher
from reports.models import SessionReport


class SessionReportFilter(filters.FilterSet):
    school = filters.NumberFilter(field_name="session__course_class__school")
    course_class = filters.NumberFilter(field_name="session__course_class")
    teacher = filters.NumberFilter(method="filter_teacher")
    date_from = filters.DateFilter(field_name="session__session_datetime", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="session__session_datetime", lookup_expr="date__lte")

    def filter_teacher(self, queryset, name, value):
        teacher_sessions = filter_sessions_for_teacher(
            CourseSession.objects.all(),
            value,
        )

        return queryset.filter(
            session__in=teacher_sessions
        )
    
    class Meta:
        model = SessionReport
        fields = [
            "school",
            "course_class",
            "teacher",
            "date_from",
            "date_to",
        ]