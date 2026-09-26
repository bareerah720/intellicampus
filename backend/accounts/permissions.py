from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
)


# =========================================================
# ADMIN
# =========================================================

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "admin"
        )


# =========================================================
# STUDENT
# =========================================================

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "student"
        )


class IsAdminOrStudent(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type in ["admin", "student"]
        )

# =========================================================
# FACULTY
# =========================================================

class IsFaculty(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "faculty"
        )


class IsAdminOrFaculty(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type in ["admin", "faculty"]
        )


# =========================================================
# STAFF
# =========================================================

class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "staff"
        )


class IsAdminOrStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type in ["admin", "staff"]
        )


# =========================================================
# OWNER OR ADMIN
# =========================================================

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):

        if not request.user.is_authenticated:
            return False

        if request.user.user_type == "admin":
            return True

        return obj.user == request.user

    from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
)


class IsAdminOrReadOnly(BasePermission):

    message = (
        "Only admin can create, update, or delete records."
    )

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        # GET, HEAD, OPTIONS
        if request.method in SAFE_METHODS:
            return True

        # POST, PUT, PATCH, DELETE
        return request.user.user_type == "admin"