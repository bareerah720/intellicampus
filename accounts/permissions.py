from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Allows access only to Admin users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "admin"
        )


class IsStudent(BasePermission):
    """
    Allows access only to Student users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "student"
        )

class IsAdminOrStudent(BasePermission):
    """
    Allows access to Admin or Student users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type in ["admin", "student"]
        )

class IsOwnerOrAdmin(BasePermission):
    """
    Admin can access any profile.
    Student can access only their own profile.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.user_type == "admin":
            return True

        return obj.user == request.user


class IsFaculty(BasePermission):
    """
    Allows access only to Faculty users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "faculty"
        )

class IsAdminOrFaculty(BasePermission):
    """
    Allows access to Admin or Faculty users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type in ["admin", "faculty"]
        )

class IsStaff(BasePermission):
    """
    Allows access only to Staff users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "staff"
        )


class IsAdminOrFaculty(BasePermission):
    """
    Allows access to Admin or Faculty users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type in ["admin", "faculty"]
        )


class IsAdminOrStaff(BasePermission):
    """
    Allows access to Admin or Staff users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type in ["admin", "staff"]
        )