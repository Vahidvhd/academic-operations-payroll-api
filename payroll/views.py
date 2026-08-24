from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from payroll.models import MonthlySalary, TeacherTermWage
from payroll.serializers import (
    MonthlySalarySerializer,
    PayrollCalculationSerializer,
    TeacherTermWageSerializer,
)
from payroll.services import calculate_all_teacher_salaries_for_month
from users.permissions import (
    IsFinanceOfficer,
    IsFinanceOfficerOrTeacher,
)


class TeacherTermWageViewSet(viewsets.ModelViewSet):
    queryset = TeacherTermWage.objects.all()
    serializer_class = TeacherTermWageSerializer
    permission_classes = [IsFinanceOfficer]
    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def perform_create(self, serializer):
        serializer.save(set_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(set_by=self.request.user)


class MonthlySalaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MonthlySalary.objects.all()
    serializer_class = MonthlySalarySerializer
    permission_classes = [IsFinanceOfficerOrTeacher]
    filterset_fields = ["year", "month"]

    def get_queryset(self):
        queryset = MonthlySalary.objects.all()

        if self.request.user.role == "teacher":
            return queryset.filter(
                teacher=self.request.user,
            )

        return queryset

    @action(detail=False, methods=["post"])
    def calculate(self, request):
        input_serializer = PayrollCalculationSerializer(
            data=request.data
        )
        input_serializer.is_valid(raise_exception=True)

        try:
            salaries = calculate_all_teacher_salaries_for_month(
                year=input_serializer.validated_data["year"],
                month=input_serializer.validated_data["month"],
                calculated_by=request.user,
            )
        except ValueError as error:
            raise ValidationError(
                {"detail": str(error)}
            )

        output_serializer = MonthlySalarySerializer(
            salaries,
            many=True,
        )

        return Response(output_serializer.data)