from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import School, Term


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ["id",
                  "name",
                  "address",
                  "created_at",
                  "updated_at"
                  ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = [
            "id",
            "start_date",
            "end_date",
            "term_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        if self.instance:
            term = Term(
                pk=self.instance.pk,
                start_date=attrs.get("start_date", self.instance.start_date),
                end_date=attrs.get("end_date", self.instance.end_date),
                term_type=attrs.get("term_type", self.instance.term_type),
            )
        else:
            term = Term(
                start_date=attrs.get("start_date"),
                end_date=attrs.get("end_date"),
                term_type=attrs.get("term_type"),
            )

        try:
            term.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        return attrs