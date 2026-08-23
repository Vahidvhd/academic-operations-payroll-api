from decimal import Decimal

from academics.models import CourseSession
from academics.services import filter_sessions_for_teacher
from reports.models import SessionReport


def calculate_session_base_amount(base_wage_rate, session_duration):
    if session_duration == 60:
        return base_wage_rate * Decimal("0.7")

    if session_duration == 90:
        return base_wage_rate

    if session_duration == 120:
        return base_wage_rate * Decimal("1.3")

    raise ValueError("Unsupported session duration.")


def apply_summer_multiplier(amount, is_summer):
    if is_summer:
        return amount * Decimal("1.1")

    return amount


def calculate_late_penalty(amount, late_hours):
    penalty_percent = min(late_hours, 100)

    return amount * Decimal(penalty_percent) / Decimal("100")


def calculate_session_amount(base_wage_rate, session_duration, is_summer, late_hours):
    base_amount = calculate_session_base_amount(
        base_wage_rate=base_wage_rate,
        session_duration=session_duration,
    )

    amount_before_penalty = apply_summer_multiplier(
        amount=base_amount,
        is_summer=is_summer,
    )
    amount_before_penalty = round(amount_before_penalty, 2)

    penalty_amount = calculate_late_penalty(
        amount=amount_before_penalty,
        late_hours=late_hours,
    )
    penalty_amount = round(penalty_amount, 2)

    amount_after_penalty = amount_before_penalty - penalty_amount
    amount_after_penalty = round(amount_after_penalty, 2)

    return (amount_before_penalty, penalty_amount, amount_after_penalty)


def get_teacher_sessions_for_month(teacher, year, month):
    sessions = CourseSession.objects.filter(
        is_deleted=False,
        session_datetime__year=year,
        session_datetime__month=month,
    )

    return filter_sessions_for_teacher(
        sessions,
        teacher.id,
    )


def get_approved_reports_for_teacher_month(teacher, year, month):
    sessions = get_teacher_sessions_for_month(
        teacher,
        year,
        month,
    )

    reports = SessionReport.objects.filter(
        session__in=sessions,
    )

    if reports.count() != sessions.count():
        raise ValueError(
            "All sessions must have a report before salary calculation."
        )

    if reports.exclude(
        status=SessionReport.Status.APPROVED
    ).exists():
        raise ValueError(
            "All reports must be approved before salary calculation."
        )

    return reports