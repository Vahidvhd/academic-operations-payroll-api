from rest_framework import viewsets

from payroll.models import TeacherTermWage
from payroll.serializers import TeacherTermWageSerializer
from users.permissions import IsFinanceOfficer


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