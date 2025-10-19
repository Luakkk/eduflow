from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from django.db.models import Count
from .models import Course, Lesson, Enrollment
from .serializers import CourseSerializer, LessonSerializer, EnrollmentSerializer
from .permissions import IsOwnerOrAdminForCourses

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return True if request.method in permissions.SAFE_METHODS else request.user.is_authenticated

class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminForCourses]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title","description"]
    ordering_fields = ["created_at","price"]

    def get_queryset(self):
        qs = Course.objects.all().annotate(lessons_count=Count("lessons"))
        user = self.request.user
        if not user.is_authenticated or user.role == "student":
            qs = qs.filter(is_published=True)
        return qs

    def perform_create(self, serializer):
        u = self.request.user
        if u.role not in ("admin","instructor"):
            raise PermissionError("Only instructors/admin can create courses.")
        serializer.save(owner=u)

    def perform_update(self, serializer):
        obj = self.get_object()
        u = self.request.user
        if u.role == "admin" or obj.owner_id == u.id:
            serializer.save()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only owner/admin can update course.")

class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Lesson.objects.select_related("course")
        u = self.request.user
        if not u.is_authenticated or u.role == "student":
            qs = qs.filter(course__is_published=True)
        return qs

    def create(self, request, *a, **kw):
        course_id = request.data.get("course")
        if not course_id:
            return Response({"detail":"course is required"}, status=400)
        from .models import Course
        course = Course.objects.filter(id=course_id).first()
        if not course: return Response({"detail":"Course not found"}, status=404)
        u = request.user
        if not u.is_authenticated: return Response({"detail":"Auth required"}, status=401)
        if u.role != "admin" and course.owner_id != u.id:
            return Response({"detail":"Only owner/admin can add lessons"}, status=403)
        return super().create(request, *a, **kw)

    def update(self, request, *a, **kw):
        obj = self.get_object()
        u = request.user
        if not u.is_authenticated: return Response({"detail":"Auth required"}, status=401)
        if u.role != "admin" and obj.course.owner_id != u.id:
            return Response({"detail":"Only owner/admin can update lessons"}, status=403)
        return super().update(request, *a, **kw)

    def destroy(self, request, *a, **kw):
        obj = self.get_object()
        u = request.user
        if not u.is_authenticated: return Response({"detail":"Auth required"}, status=401)
        if u.role != "admin" and obj.course.owner_id != u.id:
            return Response({"detail":"Only owner/admin can delete lessons"}, status=403)
        return super().destroy(request, *a, **kw)

class EnrollmentViewSet(viewsets.GenericViewSet,
                        permissions.BasePermission.__mro__[0].__bases__[0],
                        ):
    """
    POST /enrollments     (student)  -> записаться
    DELETE /enrollments/:id (student)-> отписаться
    GET /enrollments      (student/admin/instructor)
    """
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        u = self.request.user
        qs = Enrollment.objects.select_related("course")
        if not u.is_authenticated: return qs.none()
        if u.role == "student": return qs.filter(student_id=u.id)
        if u.role in ("admin","instructor"): return qs
        return qs.none()

    # mixins вручную: create / destroy / list
    from rest_framework import status
    from rest_framework.response import Response
    def list(self, request):
        ser = self.serializer_class(self.get_queryset(), many=True)
        return self.Response(ser.data)

    def create(self, request):
        u = request.user
        if u.role != "student":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only students can enroll.")
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(student=u)
        return self.Response(ser.data, status=self.status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        u = request.user
        try:
            obj = Enrollment.objects.get(id=pk)
        except Enrollment.DoesNotExist:
            return self.Response({"detail":"Not found"}, status=404)
        if u.role != "admin" and obj.student_id != u.id:
            return self.Response({"detail":"Forbidden"}, status=403)
        obj.delete()
        return self.Response(status=204)
