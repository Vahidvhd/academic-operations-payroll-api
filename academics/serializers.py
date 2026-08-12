from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import CourseClass, School, TeacherClassAssignment, Term

User = get_user_model()


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


class CourseClassSerializer(serializers.ModelSerializer):
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.filter(is_deleted=False))
    term = serializers.PrimaryKeyRelatedField(queryset=Term.objects.filter(is_deleted=False))
    class Meta:
        model = CourseClass
        fields = [
            "id",
            "school",
            "term",
            "title",
            "class_code",
            "start_date",
            "end_date",
            "session_duration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        if self.instance:
            course_class = CourseClass(
                school=attrs.get("school", self.instance.school),
                term=attrs.get("term", self.instance.term),
                title=attrs.get("title", self.instance.title),
                class_code=attrs.get("class_code", self.instance.class_code),
                start_date=attrs.get("start_date", self.instance.start_date),
                end_date=attrs.get("end_date", self.instance.end_date),
                session_duration=attrs.get(
                    "session_duration",
                    self.instance.session_duration,
                ),
            )
        else:
            course_class = CourseClass(
                school=attrs.get("school"),
                term=attrs.get("term"),
                title=attrs.get("title"),
                class_code=attrs.get("class_code"),
                start_date=attrs.get("start_date"),
                end_date=attrs.get("end_date"),
                session_duration=attrs.get("session_duration"),
            )

        try:
            course_class.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        return attrs


class TeacherClassAssignmentSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            role=User.Role.TEACHER,
            is_active=True,
        )
    )

    course_class = serializers.PrimaryKeyRelatedField(
        queryset=CourseClass.objects.filter(is_deleted=False)
    )
    class Meta:
        model = TeacherClassAssignment
        fields = [
            "id",
            "teacher",
            "course_class",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        if self.instance:
            assignment = TeacherClassAssignment(
                pk=self.instance.pk,
                teacher=attrs.get("teacher", self.instance.teacher),
                course_class=attrs.get("course_class", self.instance.course_class),
                start_date=attrs.get("start_date", self.instance.start_date),
                end_date=attrs.get("end_date", self.instance.end_date),
            )
        else:
            assignment = TeacherClassAssignment(
                teacher=attrs.get("teacher"),
                course_class=attrs.get("course_class"),
                start_date=attrs.get("start_date"),
                end_date=attrs.get("end_date"),
            )

        try:
            assignment.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        return attrs
                        