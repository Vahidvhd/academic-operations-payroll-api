from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


User = get_user_model()

class Command(BaseCommand):
    help = "Create sample users for all system roles."

    def handle(self, *args, **options):
        sample_users = (
            {
                "username": "teacher_sample",
                "first_name": "Sample",
                "last_name": "Teacher",
                "role": User.Role.TEACHER,
                "phone_number": "07000000001",
                "emergency_phone_number": "07000000002",
            },
            {
                "username": "education_sample",
                "first_name": "Sample",
                "last_name": "Education",
                "role": User.Role.EDUCATION_OFFICER,
            },
            {
                "username": "finance_sample",
                "first_name": "Sample",
                "last_name": "Finance",
                "role": User.Role.FINANCE_OFFICER,
            },
        )


        for user_data in sample_users:
            username = user_data["username"]

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f"{username} already exists.")
                )
                continue

            User.objects.create_user(**user_data, password="SamplePassword@")

            self.stdout.write(
                self.style.SUCCESS(f"{username} created successfully.")
            )


