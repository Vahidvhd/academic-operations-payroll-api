from decimal import Decimal


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