from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()

class UserModelTests(TestCase):

    def test_create_user_hashes_password(self):
        user = User.objects.create_user(
            username="teacher1",
            password="TestPassword@",
            first_name="Teacher",
            last_name="One",
            role=User.Role.TEACHER,
            phone_number="09123456789",
            emergency_phone_number="09876543211",
        )
        self.assertNotEqual(user.password, "TestPassword@")
        self.assertTrue(user.check_password("TestPassword@"))

    def test_superuser_can_exist_without_business_role(self):
        user = User.objects.create_superuser(
            username="admin",
            password="testpass123",
            first_name="Admin",
            last_name="User",
        )
        self.assertEqual(user.role, "")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_roles_have_expected_values(self):
        self.assertEqual(
            set(User.Role.values),
            {"teacher", "education_officer", "finance_officer"},
        )

    def test_business_roles_do_not_have_admin_access(self):
        for role in User.Role.values:
            user = User.objects.create_user(
                username=f"{role}_user",
                password="testpass123",
                first_name="Test",
                last_name="User",
                role=role,
            )

            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)

    def test_user_string_representation_is_username(self):
        user = User(username="teacher1")

        self.assertEqual(str(user), "teacher1")