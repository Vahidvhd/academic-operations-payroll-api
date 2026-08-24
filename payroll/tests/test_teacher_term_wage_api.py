from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from academics.models import Term
from payroll.models import TeacherTermWage

User = get_user_model()


class TeacherTermWageAPITests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher",
            role=User.Role.TEACHER,
            phone_number="07111111111",
            emergency_phone_number="07222222222",
        )

        self.finance_officer = User.objects.create_user(
            username="finance",
            role=User.Role.FINANCE_OFFICER,
        )

        self.term = Term.objects.create(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            term_type=Term.TermType.REGULAR,
        )

        self.education_officer = User.objects.create_user(
            username="education",
            role=User.Role.EDUCATION_OFFICER,
        )

        self.url = reverse("teacher-term-wage-list")

    def test_finance_officer_can_create_teacher_term_wage(self):
        self.client.force_authenticate(
            user=self.finance_officer
        )

        data = {
            "teacher": self.teacher.id,
            "term": self.term.id,
            "base_wage_rate": "200.00",
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(TeacherTermWage.objects.count(), 1)

        wage = TeacherTermWage.objects.get()

        self.assertEqual(wage.teacher, self.teacher)
        self.assertEqual(wage.term, self.term)
        self.assertEqual(wage.set_by, self.finance_officer)
        self.assertEqual(wage.base_wage_rate, Decimal("200.00"))


    def test_teacher_cannot_create_teacher_term_wage(self):
        self.client.force_authenticate(user=self.teacher)

        data = {
            "teacher": self.teacher.id,
            "term": self.term.id,
            "base_wage_rate": "200.00",
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(TeacherTermWage.objects.count(), 0)


    def test_education_officer_cannot_create_teacher_term_wage(self):
        self.client.force_authenticate(user=self.education_officer)

        data = {
            "teacher": self.teacher.id,
            "term": self.term.id,
            "base_wage_rate": "200.00",
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(TeacherTermWage.objects.count(), 0)


    def test_anonymous_user_cannot_create_teacher_term_wage(self):
        data = {
            "teacher": self.teacher.id,
            "term": self.term.id,
            "base_wage_rate": "200.00",
        }

        response = self.client.post(
            self.url,
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(TeacherTermWage.objects.count(), 0)


    def test_finance_officer_can_list_teacher_term_wages(self):
        TeacherTermWage.objects.create(
            teacher=self.teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        self.client.force_authenticate(
            user=self.finance_officer
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["teacher"],
            self.teacher.id,
        )
        self.assertEqual(
            response.data[0]["term"],
            self.term.id,
        )
        self.assertEqual(
            response.data[0]["base_wage_rate"],
            "200.00",
        )


    @patch("payroll.views.timezone")
    def test_finance_officer_can_update_wage_before_term_starts(
        self,
        mock_timezone,
    ):
        mock_timezone.localdate.return_value = date(2026, 7, 20)

        wage = TeacherTermWage.objects.create(
            teacher=self.teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        self.client.force_authenticate(
            user=self.finance_officer
        )

        url = reverse("teacher-term-wage-detail", args=[wage.id])

        response = self.client.patch(
            url,
            {
                "base_wage_rate": "220.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        wage.refresh_from_db()

        self.assertEqual(wage.base_wage_rate, Decimal("220.00"))


    @patch("payroll.views.timezone")
    def test_finance_officer_cannot_update_wage_after_term_starts(
        self,
        mock_timezone,
    ):
        mock_timezone.localdate.return_value = date(2026, 8, 10)

        wage = TeacherTermWage.objects.create(
            teacher=self.teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        self.client.force_authenticate(
            user=self.finance_officer
        )

        url = reverse("teacher-term-wage-detail", args=[wage.id])

        response = self.client.patch(
            url,
            {
                "base_wage_rate": "220.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        wage.refresh_from_db()

        self.assertEqual(wage.base_wage_rate, Decimal("200.00"))


    def test_put_is_not_allowed(self):
        wage = TeacherTermWage.objects.create(
            teacher=self.teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        self.client.force_authenticate(user=self.finance_officer)

        url = reverse("teacher-term-wage-detail", args=[wage.id])

        response = self.client.put(
            url,
            {
                "teacher": self.teacher.id,
                "term": self.term.id,
                "base_wage_rate": "250.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 405)


    def test_delete_is_not_allowed(self):
        wage = TeacherTermWage.objects.create(
            teacher=self.teacher,
            term=self.term,
            set_by=self.finance_officer,
            base_wage_rate=Decimal("200.00"),
        )

        self.client.force_authenticate(user=self.finance_officer)

        url = reverse("teacher-term-wage-detail", args=[wage.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(TeacherTermWage.objects.filter(id=wage.id).exists())