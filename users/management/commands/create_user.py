from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()

class Command(BaseCommand):
    help = "Create a user."

    def add_arguments(self, parser):
        parser.add_argument("--role", choices=User.Role.values)
        parser.add_argument("--username")
        parser.add_argument("--first-name")
        parser.add_argument("--last-name")
        parser.add_argument("--phone-number")
        parser.add_argument("--emergency-phone-number")

    def handle(self, *args, **options):
        role = options.get("role")
        if not role:
            role = input("Role: ").strip()
        if role not in User.Role.values:
            valid_roles = ", ".join(User.Role.values)
            raise CommandError(
                f"Invalid role. Choose from: {valid_roles}"
            )

        username = options.get("username")
        if not username:
            username = input("Username: ").strip()
        if not username:
            raise CommandError("Username is required.")
        if User.objects.filter(username=username).exists():
            raise CommandError("A user with this username already exists.")

        first_name = options.get("first_name")
        if not first_name:
            first_name = input("First name: ").strip()
        if not first_name:
            raise CommandError("First name is required.")

        last_name = options.get("last_name")
        if not last_name:
            last_name = input("Last name: ").strip()
        if not last_name:
            raise CommandError("Last name is required.")

        phone_number = options.get("phone_number") or ""
        emergency_phone_number = options.get("emergency_phone_number") or ""

        if role == User.Role.TEACHER and not phone_number:
            phone_number = input("Phone number: ").strip()

        if role == User.Role.TEACHER and not phone_number:
            raise CommandError("Phone number is required for teachers.")

        if role == User.Role.TEACHER and not emergency_phone_number:
            emergency_phone_number = input(
                "Emergency phone number: "
            ).strip()

        if role == User.Role.TEACHER and not emergency_phone_number:
            raise CommandError(
                "Emergency phone number is required for teachers."
            )

        password = getpass("Password: ")
        password_confirmation = getpass("Password (again): ")

        if password != password_confirmation:
            raise CommandError("Passwords do not match.")

        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone_number=phone_number,
            emergency_phone_number=emergency_phone_number,
        )

        try:
            validate_password(password, user=user)
        except ValidationError as error:
            raise CommandError("\n".join(error.messages))

        user.set_password(password)


        try:
            user.full_clean()
        except ValidationError as error:
            raise CommandError("\n".join(error.messages))

        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"User '{username}' created successfully."
            )
        )