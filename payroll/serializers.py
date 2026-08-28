from django.contrib.auth import get_user_model
from rest_framework import serializers

from academics.models import Term
from payroll.models import MonthlySalary, TeacherTermWage

User = get_user_model()


class TeacherTermWageSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            role=User.Role.TEACHER,
        )
    )
    term = serializers.PrimaryKeyRelatedField(
        queryset=Term.objects.all()
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


class PayrollCalculationSerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=1)
    month = serializers.IntegerField(min_value=1, max_value=12)


class TeacherPayrollCalculationSerializer(PayrollCalculationSerializer):
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            role=User.Role.TEACHER,
        )
    )

    
class MonthlySalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlySalary
        fields = [
            "id",
            "teacher",
            "year",
            "month",
            "gross_amount",
            "total_penalty_amount",
            "net_amount",
            "calculated_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
       