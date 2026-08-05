from unittest.mock import patch


from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase


User = get_user_model()


class CreateUserCommandTests(TestCase):
    @patch(
        "users.management.commands.create_user.getpass",
        side_effect=["testpass123", "testpass123"],
    )
    def test_create_teacher(self, mock_getpass):
        call_command(
            "create_user",
            role=User.Role.TEACHER,
            username="teacher_test",
            first_name="Teacher",
            last_name="Test",
            phone_number="09123456789",
            emergency_phone_number="09876543211",
        )

        self.assertTrue(
            User.objects.filter(username="teacher_test").exists()
        )

        user = User.objects.get(username="teacher_test")
        self.assertEqual(user.role, User.Role.TEACHER)
        self.assertEqual(user.phone_number, "09123456789")
        self.assertEqual(user.emergency_phone_number, "09876543211")
        self.assertTrue(user.check_password("testpass123"))

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="teacher_test",
            password="testpass123",
            first_name="Teacher",
            last_name="Test",
            role=User.Role.TEACHER,
            phone_number="09123456789",
            emergency_phone_number="09876543211",
        )

        self.assertRaises(
            CommandError,
            call_command,
            "create_user",
            role=User.Role.TEACHER,
            username="teacher_test",
            first_name="Teacher",
            last_name="Test",
            phone_number="09123456789",
            emergency_phone_number="09876543211",
        )