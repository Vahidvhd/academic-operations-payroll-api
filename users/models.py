from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    class Role(models.TextChoices):
        TEACHER = "teacher", "Teacher"
        EDUCATION_OFFICER = "education_officer", "Education Officer"
        FINANCE_OFFICER = "finance_officer", "Finance Officer"

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    emergency_phone_number = models.CharField(max_length=20, blank=True)

    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.username
