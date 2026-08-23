from decimal import Decimal

from django.test import SimpleTestCase

from payroll.services import (
    apply_summer_multiplier,
    calculate_late_penalty,
    calculate_session_amount,
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


class CalculateLatePenaltyTests(SimpleTestCase):
    def test_late_hours_apply_one_percent_penalty_per_hour(self):
        penalty = calculate_late_penalty(amount=Decimal("200.00"), late_hours=10)

        self.assertEqual(penalty, Decimal("20.00"))


    def test_zero_late_hours_has_no_penalty(self):
        penalty = calculate_late_penalty(amount=Decimal("200.00"), late_hours=0)

        self.assertEqual(penalty, Decimal("0.00"))


    def test_late_penalty_is_capped_at_one_hundred_percent(self):
        penalty = calculate_late_penalty(amount=Decimal("200.00"), late_hours=150)

        self.assertEqual(penalty, Decimal("200.00"))


class CalculateSessionAmountTests(SimpleTestCase):
    def test_calculates_final_session_amount(self):
        (
            amount_before_penalty,
            penalty_amount,
            amount_after_penalty,
        ) = calculate_session_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=90,
            is_summer=True,
            late_hours=10,
        )

        self.assertEqual(
            amount_before_penalty,
            Decimal("220.00"),
        )
        self.assertEqual(
            penalty_amount,
            Decimal("22.00"),
        )
        self.assertEqual(
            amount_after_penalty,
            Decimal("198.00"),
        )


    def test_rounds_session_amounts_to_two_decimal_places(self):
        (amount_before_penalty, penalty_amount, amount_after_penalty) = calculate_session_amount(
            base_wage_rate=Decimal("199.99"),
            session_duration=120,
            is_summer=True,
            late_hours=1,
        )

        self.assertEqual(amount_before_penalty, Decimal("285.99"))
        self.assertEqual(penalty_amount, Decimal("2.86"))
        self.assertEqual(amount_after_penalty, Decimal("283.13"))


    def test_one_hundred_percent_penalty_makes_final_amount_zero(self):
        (amount_before_penalty, penalty_amount, amount_after_penalty) = calculate_session_amount(
            base_wage_rate=Decimal("200.00"),
            session_duration=90,
            is_summer=False,
            late_hours=150,
        )

        self.assertEqual(amount_before_penalty, Decimal("200.00"))
        self.assertEqual(penalty_amount, Decimal("200.00"))
        self.assertEqual(amount_after_penalty, Decimal("0.00"))