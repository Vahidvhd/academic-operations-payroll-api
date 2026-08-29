from datetime import date

from django.test import TestCase

from academics.models import CourseClass, School, Term


class SoftDeleteConstraintTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

        self.term = Term.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            term_type=Term.TermType.REGULAR,
        )

    def test_school_unique_values_can_be_reused_after_soft_delete(self):
        self.school.delete()

        new_school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

        self.assertIsNotNone(new_school.id)

    def test_course_class_code_can_be_reused_after_soft_delete(self):
        course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python",
            class_code="PY101",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            session_duration=90,
        )

        course_class.delete()

        new_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python New",
            class_code="PY101",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            session_duration=90,
        )

        self.assertIsNotNone(new_course_class.id)