from django.contrib import admin
from .models import Course, Lesson, Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id","title","owner","price","is_published","created_at")
    search_fields = ("title","description")
    list_filter = ("is_published",)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("id","course","title","order_index","duration_min")
    search_fields = ("title",)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id","student","course","created_at")
    search_fields = ("student__username","course__title")
