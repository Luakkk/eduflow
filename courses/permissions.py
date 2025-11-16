from rest_framework import permissions


class CoursePermissions(permissions.BasePermission):
    """
    Permissions for CourseViewSet.

    Rules:
    - SAFE_METHODS (GET/HEAD/OPTIONS):
        * published courses: visible to everyone
        * unpublished courses: only owner or admin
    - Write operations (POST/PUT/PATCH/DELETE):
        * only admin or owner
        * create (POST) allowed only for roles: admin, instructor
    """

    def has_permission(self, request, view):
        # Read-only requests allowed for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Only admin/instructor can create courses
        if request.method == "POST":
            return getattr(user, "role", None) in ("admin", "instructor")

        # For other unsafe methods we will check per-object
        return True

    def has_object_permission(self, request, view, obj):
        # SAFE methods
        if request.method in permissions.SAFE_METHODS:
            # Published courses are visible to everyone
            if getattr(obj, "is_published", False):
                return True

            # Unpublished → only owner or admin
            user = request.user
            if not user or not user.is_authenticated:
                return False

            return getattr(user, "role", None) == "admin" or obj.owner_id == user.id

        # Write methods: only admin or owner
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return getattr(user, "role", None) == "admin" or obj.owner_id == user.id
