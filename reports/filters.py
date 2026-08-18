from django_filters import rest_framework as filters

from reports.models import SessionReport


class SessionReportFilter(filters.FilterSet):
    school = filters.NumberFilter(
        field_name="session__course_class__school"
    )

    class Meta:
        model = SessionReport
        fields = ["school"]