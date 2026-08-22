from django.contrib.auth import get_user_model
from rest_framework import serializers

from academics.models import Term
from payroll.models import TeacherTermWage


User = get_user_model()


class TeacherTermWageSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            role=User.Role.TEACHER,
            is_active=True,
        )
    )
    term = serializers.PrimaryKeyRelatedField(
        queryset=Term.objects.filter(is_deleted=False)
    )

    class Meta:
        model = TeacherTermWage
        fields = [
            "id",
            "teacher",
            "term",
            "set_by",
            "base_wage_rate",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "set_by",
            "created_at",
            "updated_at",
        ]