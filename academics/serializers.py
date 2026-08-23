from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import (
    CourseClass,
    CourseSession,
    School,
    TeacherClassAssignment,
    Term,
)

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


class TeacherSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
        ]


class CourseClassDetailSerializer(CourseClassSerializer):
    current_teacher = serializers.SerializerMethodField()

    class Meta(CourseClassSerializer.Meta):
        fields = CourseClassSerializer.Meta.fields + [
            "current_teacher",
        ]

    def get_current_teacher(self, obj):
        today = timezone.localdate()

        assignments = obj.teacher_assignments.filter(
            start_date__lte=today
        ).exclude(
            end_date__lt=today
        )

        current_assignment = assignments.first()

        if current_assignment is None:
            return None
        
        return TeacherSummarySerializer(current_assignment.teacher).data

    
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


class CourseSessionSerializer(serializers.ModelSerializer):
    course_class = serializers.PrimaryKeyRelatedField(
        queryset=CourseClass.objects.filter(is_deleted=False)
    )

    class Meta:
        model = CourseSession
        fields = [
            "id",
            "course_class",
            "conducted_by",
            "session_datetime",
            "session_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


    def validate(self, attrs):
        if self.instance:
            session = CourseSession(
                pk=self.instance.pk,
                course_class=attrs.get(
                    "course_class",
                    self.instance.course_class,
                ),
                conducted_by=attrs.get(
                    "conducted_by",
                    self.instance.conducted_by,
                ),
                session_datetime=attrs.get(
                    "session_datetime",
                    self.instance.session_datetime,
                ),
                session_number=attrs.get(
                    "session_number",
                    self.instance.session_number,
                ),
            )
        else:
            session = CourseSession(
                course_class=attrs.get("course_class"),
                conducted_by=attrs.get("conducted_by"),
                session_datetime=attrs.get("session_datetime"),
                session_number=attrs.get("session_number"),
            )

        existing_sessions = CourseSession.objects.filter(
            course_class=session.course_class,
            session_number=session.session_number,
            is_deleted=False,
        )

        if self.instance:
            existing_sessions = existing_sessions.exclude(pk=self.instance.pk)

        if existing_sessions.exists():
            raise serializers.ValidationError(
                {
                    "session_number": (
                        "Session number must be unique for this class."
                    )
                }
            )

        try:
            session.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        return attrs