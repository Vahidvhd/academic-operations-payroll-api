from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "role",
        )


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.Role.choices, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "emergency_phone_number",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        role = attrs.get("role")
        phone_number = attrs.get("phone_number", "")
        emergency_phone_number = attrs.get("emergency_phone_number", "")

        if role == User.Role.TEACHER:
            if not phone_number.strip():
                raise serializers.ValidationError(
                    {
                        "phone_number": (
                            "Phone number is required for teachers."
                        )
                    }
                )

            if not emergency_phone_number.strip():
                raise serializers.ValidationError(
                    {
                        "emergency_phone_number": (
                            "Emergency phone number is required for teachers."
                        )
                    }
                )

        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            **validated_data
        )

    
    