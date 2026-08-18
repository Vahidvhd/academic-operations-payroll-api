from django.db.models import F, Q
from django_filters import rest_framework as filters

from reports.models import SessionReport


class SessionReportFilter(filters.FilterSet):
    school = filters.NumberFilter(field_name="session__course_class__school")
    course_class = filters.NumberFilter(field_name="session__course_class")
    teacher = filters.NumberFilter(method="filter_teacher")
    date_from = filters.DateFilter(field_name="session__session_datetime", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="session__session_datetime", lookup_expr="date__lte")

    def filter_teacher(self, queryset, name, value):
        return queryset.filter(
            Q(
                session__course_class__teacher_assignments__end_date__isnull=True
            )
            | Q(
                session__session_datetime__date__lte=F(
                    "session__course_class__teacher_assignments__end_date"
                )
            ),
            session__course_class__teacher_assignments__teacher_id=value,
            session__session_datetime__date__gte=F(
                "session__course_class__teacher_assignments__start_date"
            ),
        ).distinct()
    
    class Meta:
        model = SessionReport
        fields = [
            "school",
            "course_class",
            "teacher",
            "date_from",
            "date_to",
        ]