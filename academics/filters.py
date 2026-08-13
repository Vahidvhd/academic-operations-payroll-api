from django_filters import rest_framework as filters

from .models import CourseClass


class CourseClassFilter(filters.FilterSet):
    teacher = filters.NumberFilter(
        field_name="teacher_assignments__teacher",
        distinct=True,
    )

    class Meta:
        model = CourseClass
        fields = ["school", "term", "teacher"]