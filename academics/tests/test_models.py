from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from academics.models import (
    CourseClass,
    CourseSession,
    School,
    TeacherClassAssignment,
    Term,
)

User = get_user_model()


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


class TeacherClassAssignmentModelTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher1",
            password="testpass123",
            first_name="Test",
            last_name="Teacher",
            role=User.Role.TEACHER,
        )

        self.school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

        self.term = Term.objects.create(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            term_type=Term.TermType.REGULAR,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY-101",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            session_duration=CourseClass.SessionDuration.NINETY,
        )


    def test_end_date_cannot_be_before_start_date(self):
        assignment = TeacherClassAssignment(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 20),
            end_date=date(2026, 3, 10),
        )

        self.assertRaises(ValidationError, assignment.full_clean)


    def test_assignment_cannot_start_before_class(self):
        assignment = TeacherClassAssignment(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 2, 28),
            end_date=date(2026, 3, 10),
        )

        self.assertRaises(ValidationError, assignment.full_clean)


    def test_assignment_cannot_end_after_class(self):
        assignment = TeacherClassAssignment(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 10),
            end_date=date(2026, 4, 1),
        )

        self.assertRaises(ValidationError, assignment.full_clean)


    def test_assignment_cannot_start_after_class(self):
        assignment = TeacherClassAssignment(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 5),
        )

        self.assertRaises(ValidationError, assignment.full_clean)


    def test_selected_user_must_have_teacher_role(self):
        education_officer = User.objects.create_user(
            username="education1",
            password="testpass123",
            first_name="Test",
            last_name="Officer",
            role=User.Role.EDUCATION_OFFICER,
        )

        assignment = TeacherClassAssignment(
            teacher=education_officer,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
        )

        self.assertRaises(ValidationError, assignment.full_clean)


    def test_assignments_for_same_class_cannot_overlap(self):
        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            password="testpass123",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
        )

        overlapping_assignment = TeacherClassAssignment(
            teacher=second_teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 5),
            end_date=date(2026, 3, 15),
        )

        self.assertRaises(ValidationError, overlapping_assignment.full_clean)


    def test_open_assignment_cannot_overlap_with_new_assignment(self):
        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=None,
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            password="testpass123",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
        )

        overlapping_assignment = TeacherClassAssignment(
            teacher=second_teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 15),
            end_date=date(2026, 3, 20),
        )

        self.assertRaises(ValidationError, overlapping_assignment.full_clean)


    def test_sequential_assignments_are_allowed(self):
        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            password="testpass123",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
        )

        assignment = TeacherClassAssignment(
            teacher=second_teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 11),
            end_date=date(2026, 3, 20),
        )

        assignment.full_clean()


    def test_same_teacher_can_be_assigned_again_later(self):
        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            password="testpass123",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
        )

        TeacherClassAssignment.objects.create(
            teacher=second_teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 11),
            end_date=date(2026, 3, 20),
        )

        returning_assignment = TeacherClassAssignment(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 21),
            end_date=date(2026, 3, 31),
        )

        returning_assignment.full_clean()


    def test_assignment_can_be_updated_without_overlapping_with_itself(self):
        assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
        )

        assignment.end_date = date(2026, 3, 12)

        assignment.full_clean()


    def test_assignments_for_different_classes_can_overlap(self):
        second_course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Django Basics",
            class_code="DJ-101",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            session_duration=CourseClass.SessionDuration.NINETY,
        )

        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 20),
        )

        assignment = TeacherClassAssignment(
            teacher=self.teacher,
            course_class=second_course_class,
            start_date=date(2026, 3, 10),
            end_date=date(2026, 3, 25),
        )

        assignment.full_clean()


    def test_assignments_cannot_share_the_same_boundary_date(self):
        TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            password="testpass123",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
        )

        assignment = TeacherClassAssignment(
            teacher=second_teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 10),
            end_date=date(2026, 3, 20),
        )

        self.assertRaises(ValidationError, assignment.full_clean)


    def test_updating_assignment_cannot_create_overlap(self):
        first_assignment = TeacherClassAssignment.objects.create(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
        )

        second_teacher = User.objects.create_user(
            username="teacher2",
            password="testpass123",
            first_name="Second",
            last_name="Teacher",
            role=User.Role.TEACHER,
        )

        TeacherClassAssignment.objects.create(
            teacher=second_teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 15),
            end_date=date(2026, 3, 25),
        )

        first_assignment.end_date = date(2026, 3, 20)

        self.assertRaises(ValidationError, first_assignment.full_clean)


    def test_assignment_can_have_no_end_date(self):
        assignment = TeacherClassAssignment(
            teacher=self.teacher,
            course_class=self.course_class,
            start_date=date(2026, 3, 1),
            end_date=None,
        )

        assignment.full_clean()


class CourseSessionModelTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

        self.term = Term.objects.create(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            term_type=Term.TermType.REGULAR,
        )

        self.course_class = CourseClass.objects.create(
            school=self.school,
            term=self.term,
            title="Python Basics",
            class_code="PY-101",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            session_duration=CourseClass.SessionDuration.NINETY,
        )


    def test_string_representation(self):
        session = CourseSession(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(datetime(2026, 3, 10, 10, 0)),
            session_number=1,
        )

        self.assertEqual(str(session),"Python Basics (PY-101) - Session 1")


    def test_session_cannot_be_before_class_start_date(self):
        session = CourseSession(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(datetime(2026, 2, 28, 10, 0)),
            session_number=1,
        )

        self.assertRaises(ValidationError, session.full_clean)


    def test_session_cannot_be_after_class_end_date(self):
        session = CourseSession(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 4, 1, 10, 0)
            ),
            session_number=1,
        )

        self.assertRaises(ValidationError, session.full_clean)


    def test_session_number_must_be_at_least_one(self):
        session = CourseSession(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 3, 10, 10, 0)
            ),
            session_number=0,
        )

        self.assertRaises(ValidationError, session.full_clean)


    def test_session_number_must_be_unique_per_course_class(self):
        CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 3, 10, 10, 0)
            ),
            session_number=1,
        )

        duplicate_session = CourseSession(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 3, 12, 10, 0)
            ),
            session_number=1,
        )

        self.assertRaises(ValidationError, duplicate_session.full_clean)


    def test_sessions_for_same_class_cannot_overlap(self):
        CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 3, 10, 10, 0)
            ),
            session_number=1,
        )

        overlapping_session = CourseSession(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 3, 10, 11, 0)
            ),
            session_number=2,
        )

        self.assertRaises(
            ValidationError,
            overlapping_session.full_clean,
        )


    def test_sessions_can_be_back_to_back(self):
        CourseSession.objects.create(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 3, 10, 10, 0)
            ),
            session_number=1,
        )

        second_session = CourseSession(
            course_class=self.course_class,
            session_datetime=timezone.make_aware(
                datetime(2026, 3, 10, 11, 30)
            ),
            session_number=2,
        )

        second_session.full_clean()