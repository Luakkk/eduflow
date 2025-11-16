from rest_framework import viewsets, mixins, filters, permissions, status, generics
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import logging

from .models import Course, Lesson, Enrollment
from .serializers import CourseSerializer, LessonSerializer, EnrollmentSerializer
from .permissions import CoursePermissions

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 5, cache="default"), name="dispatch")
class CourseListView(generics.ListAPIView):
    """
    Read-only list of courses (with optional caching).

    Separate endpoint that can be used for a cached public course listing.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]


class CourseViewSet(viewsets.ModelViewSet):
    """
    Main CRUD API for courses.

    Rules:
    - Anonymous users and students:
        * can list and view only published courses.
    - Instructors and admins:
        * can create courses.
        * can update/delete their own courses.
    - Admins:
        * full access to all courses.
    """
    serializer_class = CourseSerializer
    permission_classes = [CoursePermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "price"]

    def get_queryset(self):
        qs = Course.objects.all().annotate(lessons_count=Count("lessons"))
        user = self.request.user

        # Anonymous users and students see only published courses
        if not user.is_authenticated or getattr(user, "role", None) == "student":
            qs = qs.filter(is_published=True)

        return qs

    def perform_create(self, serializer):
        """
        Creation is allowed only for instructors and admins.
        """
        user = self.request.user
        role = getattr(user, "role", None)

        # Double-check (permissions should already block this)
        if not user.is_authenticated or role not in ("admin", "instructor"):
            raise PermissionDenied("Only instructors or admins can create courses.")

        serializer.save(owner=user)

    def perform_update(self, serializer):
        """
        Object-level permissions are handled by CoursePermissions.
        """
        serializer.save()


class LessonViewSet(viewsets.ModelViewSet):
    """
    CRUD for lessons.

    - Anyone can read lessons of published courses.
    - Only course owner or admin can create/update/delete lessons.
    """
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Lesson.objects.select_related("course")
        user = self.request.user

        # Anonymous users and students only see lessons of published courses
        if not user.is_authenticated or getattr(user, "role", None) == "student":
            qs = qs.filter(course__is_published=True)

        return qs

    def create(self, request, *args, **kwargs):
        course_id = request.data.get("course")
        if not course_id:
            return Response(
                {"detail": "course is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response(
                {"detail": "Course not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if getattr(user, "role", None) != "admin" and course.owner_id != user.id:
            return Response(
                {"detail": "Only owner or admin can add lessons"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if getattr(user, "role", None) != "admin" and obj.course.owner_id != user.id:
            return Response(
                {"detail": "Only owner or admin can update lessons"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if getattr(user, "role", None) != "admin" and obj.course.owner_id != user.id:
            return Response(
                {"detail": "Only owner or admin can delete lessons"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)


class EnrollmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Enrollment API.

    - POST   /enrollments/       (student)  -> enroll to a course
    - DELETE /enrollments/{id}/  (student)  -> unenroll from a course
    - GET    /enrollments/       (student/admin/instructor)

    Student sees only their own enrollments.
    Instructors/admins can see all enrollments.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Enrollment.objects.select_related("course")

        if not user.is_authenticated:
            return qs.none()

        role = getattr(user, "role", None)

        if role == "student":
            return qs.filter(student_id=user.id)

        if role in ("admin", "instructor"):
            return qs

        return qs.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if getattr(user, "role", None) != "student":
            raise PermissionDenied("Only students can enroll.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(student=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()

        # Only admin or the student who owns the enrollment can delete it
        if getattr(user, "role", None) != "admin" and instance.student_id != user.id:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
