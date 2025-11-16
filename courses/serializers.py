from rest_framework import serializers
from .models import Course, Lesson, Enrollment


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model.

    Responsibilities:
    - expose owner username as read-only
    - provide lessons_count annotation (from queryset annotation)
    - validate title length
    - validate that price is not negative
    """
    owner = serializers.ReadOnlyField(source="owner.username")
    lessons_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "description",
            "price",
            "is_published",
            "owner",
            "created_at",
            "lessons_count",
        )
        read_only_fields = ("id", "owner", "created_at", "lessons_count")

    def validate_title(self, value: str) -> str:
        """
        Title must be at least 3 non-space characters.
        """
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value

    def validate_price(self, value):
        """
        Price cannot be negative.
        """
        if value < 0:
            raise serializers.ValidationError("Price must be >= 0.")
        return value


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for Lesson model.

    Responsibilities:
    - validate minimal duration
    - validate title length
    """
    class Meta:
        model = Lesson
        fields = ("id", "course", "title", "content", "duration_min", "order_index")
        read_only_fields = ("id",)

    def validate_duration_min(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("Duration must be >= 1 minute.")
        return value

    def validate_title(self, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value


class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Enrollment model.

    Responsibilities:
    - prevent creating duplicate enrollments (same student + course)
    - make student and created_at read-only from API
    """
    class Meta:
        model = Enrollment
        fields = ("id", "student", "course", "created_at")
        read_only_fields = ("id", "student", "created_at")

    def validate(self, attrs):
        """
        Optional duplicate check:
        if request is available in context and user is authenticated,
        do not allow enrolling twice into the same course.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        course = attrs.get("course")

        if user is not None and user.is_authenticated and course is not None:
            if Enrollment.objects.filter(student=user, course=course).exists():
                raise serializers.ValidationError(
                    {"non_field_errors": ["You are already enrolled in this course."]}
                )
        return attrs
