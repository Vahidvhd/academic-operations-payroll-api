from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from academics.models import School, Term, CourseClass


class SchoolModelTests(TestCase):
    def test_string_representation(self):
        school = School.objects.create(name="Test School", address="Test Address")

        self.assertEqual(str(school), "Test School")

    def test_name_and_address_combination_must_be_unique(self):
        School.objects.create(name="Test School", address="Test Address")

        duplicate_school = School(name="Test School", address="Test Address")

        self.assertRaises(ValidationError, duplicate_school.full_clean)


class TermModelTests(TestCase):
    def test_string_representation(self):
        term = Term.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            term_type=Term.TermType.REGULAR,
        )

        self.assertEqual(str(term), "Regular (2026-01-01 - 2026-01-31)")

    def test_end_date_cannot_be_before_start_date(self):
        term = Term(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 1, 31),
            term_type=Term.TermType.REGULAR,
        )

        self.assertRaises(ValidationError, term.full_clean)

    def test_start_date_must_be_first_day_of_month(self):
        term = Term(
            start_date=date(2026, 2, 2),
            end_date=date(2026, 2, 28),
            term_type=Term.TermType.REGULAR,
        )

        self.assertRaises(ValidationError, term.full_clean)

    def test_end_date_must_be_last_day_of_month(self):
        term = Term(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 27),
            term_type=Term.TermType.REGULAR,
        )

        self.assertRaises(ValidationError, term.full_clean)

    def test_term_dates_cannot_overlap(self):
        Term.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            term_type=Term.TermType.REGULAR,
        )

        overlapping_term = Term(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28),
            term_type=Term.TermType.REGULAR,
        )

        self.assertRaises(ValidationError, overlapping_term.full_clean)



class CourseClassModelTests(TestCase):
    def test_string_representation(self):
        school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

        term = Term.objects.create(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            term_type=Term.TermType.REGULAR,
        )

        course_class = CourseClass.objects.create(
            school=school,
            term=term,
            title="Python Basics",
            class_code="PY-101",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            session_duration=CourseClass.SessionDuration.NINETY,
        )

        self.assertEqual(str(course_class), "Python Basics (PY-101)")


    def test_end_date_cannot_be_before_start_date(self):
        school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

        term = Term.objects.create(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            term_type=Term.TermType.REGULAR,
        )

        course_class = CourseClass(
            school=school,
            term=term,
            title="Python Basics",
            class_code="PY-101",
            start_date=date(2026, 3, 20),
            end_date=date(2026, 3, 10),
            session_duration=CourseClass.SessionDuration.NINETY,
        )

        self.assertRaises(ValidationError, course_class.full_clean)

    def test_class_cannot_start_before_term(self):
        school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

        term = Term.objects.create(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            term_type=Term.TermType.REGULAR,
        )

        course_class = CourseClass(
            school=school,
            term=term,
            title="Python Basics",
            class_code="PY-101",
            start_date=date(2026, 2, 28),
            end_date=date(2026, 3, 20),
            session_duration=CourseClass.SessionDuration.NINETY,
        )

        self.assertRaises(ValidationError, course_class.full_clean)

    def test_class_cannot_end_after_term(self):
        school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

        term = Term.objects.create(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            term_type=Term.TermType.REGULAR,
        )

        course_class = CourseClass(
            school=school,
            term=term,
            title="Python Basics",
            class_code="PY-101",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 4, 1),
            session_duration=CourseClass.SessionDuration.NINETY,
        )

        self.assertRaises(ValidationError, course_class.full_clean)