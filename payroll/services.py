from decimal import Decimal

from django.db import transaction

from academics.models import CourseSession, Term
from academics.services import filter_sessions_for_teacher
from payroll.models import MonthlySalary, MonthlySalaryItem, TeacherTermWage
from reports.models import SessionReport
from users.models import User


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

    reports = SessionReport.objects.filter(session__in=sessions).select_related("session__course_class__term")

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


def get_teacher_term_wage(teacher, term):
    try:
        return TeacherTermWage.objects.get(
            teacher=teacher,
            term=term,
        )
    except TeacherTermWage.DoesNotExist:
        raise ValueError(
            f"Base wage is not set for teacher {teacher.id} and term {term.id}."
        )


def calculate_report_amount(report, teacher):
    course_class = report.session.course_class
    term = course_class.term

    wage = get_teacher_term_wage(
        teacher,
        term,
    )

    is_summer = term.term_type == Term.TermType.SUMMER

    return calculate_session_amount(
        base_wage_rate=wage.base_wage_rate,
        session_duration=course_class.session_duration,
        is_summer=is_summer,
        late_hours=report.late_hours,
    )


def calculate_teacher_month_totals(teacher, year, month):
    reports = get_approved_reports_for_teacher_month(
        teacher,
        year,
        month,
    )

    gross_amount = Decimal("0.00")
    total_penalty_amount = Decimal("0.00")
    net_amount = Decimal("0.00")

    for report in reports:
        (
            amount_before_penalty,
            penalty_amount,
            amount_after_penalty,
        ) = calculate_report_amount(
            report,
            teacher,
        )

        gross_amount += amount_before_penalty
        total_penalty_amount += penalty_amount
        net_amount += amount_after_penalty

    return (
        gross_amount,
        total_penalty_amount,
        net_amount,
    )


def calculate_teacher_monthly_salary(teacher, year, month, calculated_by):
    existing_salary = MonthlySalary.objects.filter(
        teacher=teacher,
        year=year,
        month=month,
    ).first()

    sessions = get_teacher_sessions_for_month(
        teacher,
        year,
        month,
    )

    if not sessions.exists():
        return None

    reports = get_approved_reports_for_teacher_month(
        teacher,
        year,
        month,
    )

    (
        gross_amount,
        total_penalty_amount,
        net_amount,
    ) = calculate_teacher_month_totals(
        teacher,
        year,
        month,
    )

    with transaction.atomic():
        if existing_salary:
            salary = existing_salary
            salary.calculated_by = calculated_by
            salary.gross_amount = gross_amount
            salary.total_penalty_amount = total_penalty_amount
            salary.net_amount = net_amount
            salary.save()
        else:
            salary = MonthlySalary.objects.create(
                teacher=teacher,
                year=year,
                month=month,
                calculated_by=calculated_by,
                gross_amount=gross_amount,
                total_penalty_amount=total_penalty_amount,
                net_amount=net_amount,
            )

        MonthlySalaryItem.objects.filter(
            monthly_salary=salary,
        ).delete()

        for report in reports:
            (
                amount_before_penalty,
                penalty_amount,
                amount_after_penalty,
            ) = calculate_report_amount(
                report,
                teacher,
            )

            MonthlySalaryItem.objects.create(
                monthly_salary=salary,
                session_report=report,
                amount_before_penalty=amount_before_penalty,
                penalty_amount=penalty_amount,
                amount_after_penalty=amount_after_penalty,
            )

    return salary


def get_teachers_for_month(year, month):
    sessions = CourseSession.objects.filter(
        is_deleted=False,
        session_datetime__year=year,
        session_datetime__month=month,
    )

    teacher_ids = set()

    for session in sessions:
        teacher = session.get_effective_teacher()

        if teacher:
            teacher_ids.add(teacher.id)

    return User.objects.filter(id__in=teacher_ids)


def calculate_all_teacher_salaries_for_month(year, month, calculated_by):
    teachers = get_teachers_for_month(year, month)
    salaries = []

    with transaction.atomic():
        for teacher in teachers:
            try:
                get_approved_reports_for_teacher_month(
                    teacher,
                    year,
                    month,
                )
            except ValueError:
                continue

            salary = calculate_teacher_monthly_salary(
                teacher,
                year,
                month,
                calculated_by,
            )

            salaries.append(salary)

    return salaries