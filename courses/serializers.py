from rest_framework import serializers
from django.db.models import Count
from .models import Course, Lesson, Enrollment

class CourseSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    lessons_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Course
        fields = ("id","title","description","price","is_published","owner","created_at","lessons_count")
        read_only_fields = ("id","owner","created_at","lessons_count")
    def validate_title(self, v):
        if len(v) < 3: raise serializers.ValidationError("Title must be at least 3 chars.")
        return v

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ("id","course","title","content","duration_min","order_index")
        read_only_fields = ("id",)
    def validate_duration_min(self, v):
        if v < 1: raise serializers.ValidationError("Duration must be >= 1 minute.")
        return v

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ("id","student","course","created_at")
        read_only_fields = ("id","student","created_at")
