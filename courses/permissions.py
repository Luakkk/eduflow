from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAdminForCourses(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS: return True
        if request.user.is_authenticated and request.user.role == "admin": return True
        return request.user.is_authenticated and getattr(obj, "owner_id", None) == request.user.id
