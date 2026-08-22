from decimal import Decimal

from django.test import SimpleTestCase

from payroll.services import (
    apply_summer_multiplier,
    calculate_session_base_amount,
)


class CalculateSessionBaseAmountTests(SimpleTestCase):
    def test_ninety_minute_session_uses_full_base_wage(self):
        amount = calculate_session_base_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=90,
        )

        self.assertEqual(amount, Decimal("200.00"))

    def test_sixty_minute_session_uses_seventy_percent_of_base_wage(self):
        amount = calculate_session_base_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=60,
        )

        self.assertEqual(amount, Decimal("140.00"))

    def test_one_hundred_twenty_minute_session_uses_one_hundred_thirty_percent_of_base_wage(self):
        amount = calculate_session_base_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=120,
        )

        self.assertEqual(amount, Decimal("260.00"))

    def test_unsupported_session_duration_raises_value_error(self):
        try:
            calculate_session_base_amount(
                base_wage_rate=Decimal("200.00"),
                session_duration=75,
            )
        except ValueError as error:
            self.assertEqual(
                str(error),
                "Unsupported session duration.",
            )
        else:
            self.fail("ValueError was not raised.")


class ApplySummerMultiplierTests(SimpleTestCase):
    def test_summer_term_increases_amount_by_ten_percent(self):
        amount = apply_summer_multiplier(
            amount=Decimal("200.00"),
            is_summer=True,
        )

        self.assertEqual(amount, Decimal("220.00"))


    def test_non_summer_term_keeps_amount_unchanged(self):
        amount = apply_summer_multiplier(
            amount=Decimal("200.00"),
            is_summer=False,
        )

        self.assertEqual(amount, Decimal("200.00"))