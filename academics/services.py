from django.db.models import F, Q


def filter_sessions_for_teacher(queryset, teacher_id):
    return queryset.filter(
        Q(conducted_by_id=teacher_id)
        | (
            Q(conducted_by__isnull=True)
            & Q(
                course_class__teacher_assignments__teacher_id=teacher_id
            )
            & Q(
                session_datetime__date__gte=F(
                    "course_class__teacher_assignments__start_date"
                )
            )
            & (
                Q(
                    course_class__teacher_assignments__end_date__isnull=True
                )
                | Q(
                    session_datetime__date__lte=F(
                        "course_class__teacher_assignments__end_date"
                    )
                )
            )
        )
    ).distinct()