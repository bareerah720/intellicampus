import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken


from .permissions import (
    IsAdmin,
    IsAdminOrStudent,
    IsAdminOrFaculty,
    IsAdminOrStaff,
    IsFaculty,
    IsStaff,
    IsOwnerOrAdmin,
    IsAdminOrReadOnly,
)

from rest_framework.permissions import SAFE_METHODS


from .models import (
    User,
    Department,
    Program,
    Semester,
    AcademicSession,
    Office,
    Batch,
    StudentProfile,
    FacultyProfile,
    StaffProfile,
    ResponsibilityAssignment,
)

from .serializers import (
    UserSerializer,
    DepartmentSerializer,
    ProgramSerializer,
    SemesterSerializer,
    AcademicSessionSerializer,
    OfficeSerializer,
    BatchSerializer,
    ChangePasswordSerializer,
    StudentProfileSerializer,
    FacultyProfileSerializer,
    StaffProfileSerializer,
    ResponsibilityAssignmentSerializer,
    StudentLoginSerializer,
    EmailLoginSerializer,
    AdminUserCreateSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer,
    AdminUserManagementSerializer,
    AdminSetPasswordSerializer,
)

logger = logging.getLogger(__name__)


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        request_data = getattr(request, "data", None)
        if request_data is None:
            request_data = getattr(request, "POST", {})
        identifier = (
            request_data.get("email")
            or request_data.get("registration_number")
            or ""
        )
        identifier = str(identifier).strip().casefold()
        if not identifier:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"{self.get_ident(request)}:{identifier}",
        }


class AdminWritesMixin:

    def get_permissions(self):

        if self.request.method not in SAFE_METHODS:
            return [IsAdmin()]

        return super().get_permissions()


class OwnProfileQuerysetMixin:

    def get_queryset(self):

        queryset = super().get_queryset()

        user = self.request.user

        if user.user_type == "admin":
            return queryset

        return queryset.filter(user=user)
class UserListCreateView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]


class AdminUserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.select_related(
        "faculty_profile__department",
        "faculty_profile__office",
        "staff_profile__office",
    )
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdmin]


class AdminUserManagementView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.select_related(
        "faculty_profile__department",
        "faculty_profile__office",
        "staff_profile__office",
    )
    serializer_class = AdminUserManagementSerializer
    permission_classes = [IsAdmin]

    def perform_update(self, serializer):
        with transaction.atomic():
            serializer.save()


class AdminUserCreateView(generics.CreateAPIView):
    serializer_class = AdminUserCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "User and role profile created successfully.",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
            },
            status=status.HTTP_201_CREATED
        )

class DepartmentListCreateView(
    generics.ListCreateAPIView
):

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    permission_classes = [IsAdminOrReadOnly]
class DepartmentDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    permission_classes = [IsAdminOrReadOnly]


class ProgramListCreateView(generics.ListCreateAPIView):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAdminOrReadOnly]
class ProgramDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAdminOrReadOnly]

class SemesterListCreateView(generics.ListCreateAPIView):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [IsAdminOrReadOnly]
class SemesterDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [IsAdminOrReadOnly]

class AcademicSessionListCreateView(generics.ListCreateAPIView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsAdminOrReadOnly]
class AcademicSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsAdminOrReadOnly]

class OfficeListCreateView(generics.ListCreateAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAdminOrReadOnly]
class OfficeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAdminOrReadOnly]

class BatchListCreateView(generics.ListCreateAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAdminOrReadOnly]
class BatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAdminOrReadOnly]

class StudentProfileListCreateView(
    AdminWritesMixin,
    OwnProfileQuerysetMixin,
    generics.ListCreateAPIView
):

    queryset = StudentProfile.objects.all()

    serializer_class = StudentProfileSerializer

    permission_classes = [IsAdminOrStudent]


class StudentProfileDetailView(
    AdminWritesMixin,
    OwnProfileQuerysetMixin,
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = StudentProfile.objects.all()

    serializer_class = StudentProfileSerializer

    permission_classes = [
        IsAdminOrStudent,
        IsOwnerOrAdmin,
    ]

class FacultyProfileListCreateView(
    AdminWritesMixin,
    OwnProfileQuerysetMixin,
    generics.ListCreateAPIView):
    queryset = FacultyProfile.objects.all()
    serializer_class = FacultyProfileSerializer
    permission_classes = [IsAdminOrFaculty]

class FacultyProfileDetailView(
    AdminWritesMixin,
    OwnProfileQuerysetMixin,
    generics.RetrieveUpdateDestroyAPIView):
    queryset = FacultyProfile.objects.all()
    serializer_class = FacultyProfileSerializer
    permission_classes = [IsAdminOrFaculty, IsOwnerOrAdmin]


class StaffProfileListCreateView(
    AdminWritesMixin,
    OwnProfileQuerysetMixin,
    generics.ListCreateAPIView
):

    queryset = StaffProfile.objects.all()

    serializer_class = StaffProfileSerializer

    permission_classes = [IsAdminOrStaff]


class StaffProfileDetailView(
    AdminWritesMixin,
    OwnProfileQuerysetMixin,
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = StaffProfile.objects.all()

    serializer_class = StaffProfileSerializer

    permission_classes = [
        IsAdminOrStaff,
        IsOwnerOrAdmin,
    ]

class ResponsibilityAssignmentListCreateView(
    generics.ListCreateAPIView
):

    queryset = ResponsibilityAssignment.objects.all()

    serializer_class = (
        ResponsibilityAssignmentSerializer
    )

    permission_classes = [IsAdmin]


class ResponsibilityAssignmentDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = ResponsibilityAssignment.objects.all()

    serializer_class = (
        ResponsibilityAssignmentSerializer
    )

    permission_classes = [IsAdmin]

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        with transaction.atomic():
            serializer.save()

# =========================================================
# STUDENT LOGIN VIEW
# =========================================================

class StudentLoginView(generics.GenericAPIView):

    serializer_class = StudentLoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        student_profile = serializer.validated_data["student_profile"]

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Student login successful.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),

                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "must_change_password": user.must_change_password,
                    "user_type": user.user_type,
                },

                "student": {
                    "id": student_profile.id,
                    "registration_number": student_profile.registration_number,
                    "program": student_profile.program_id,
                    "batch": student_profile.batch_id,
                    "current_semester": student_profile.current_semester_id,
                    "cgpa": str(student_profile.cgpa),
                    "profile_completed": student_profile.profile_completed,
                },
            },
            status=status.HTTP_200_OK
        )

# =========================================================
# CHANGE PASSWORD VIEW
# =========================================================

class ChangePasswordView(generics.GenericAPIView):

    serializer_class = ChangePasswordSerializer

    permission_classes = [IsAuthenticated]

    def post(self, request):

        # Validate request data
        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        # Get logged-in user
        user = request.user

        # Get new password
        new_password = serializer.validated_data[
            "new_password"
        ]

        # Hash and set new password
        user.set_password(new_password)

        # First-login password requirement completed
        user.must_change_password = False

        # Save changes in PostgreSQL
        user.save(
            update_fields=[
                "password",
                "must_change_password",
                "updated_at",
            ]
        )

        return Response(
            {
                "message": "Password changed successfully.",
                "must_change_password": False,
            },
            status=status.HTTP_200_OK
        )

# =========================================================
# EMAIL LOGIN VIEW (FACULTY / STAFF / ADMIN / EXAMINER)
# =========================================================

class EmailLoginView(generics.GenericAPIView):

    serializer_class = EmailLoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "user_type": user.user_type,
                    "must_change_password": user.must_change_password,
                },
            },
            status=status.HTTP_200_OK,
        )



def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}"
        f"/reset-password/{uid}/{token}"
    )
    send_mail(
        subject="Reset your IntelliCampus password",
        message=(
            "We received a request to reset your IntelliCampus password. "
            "Use the link below to choose a new password.\n\n"
            f"{reset_url}\n\n"
            "If you did not request this, you can ignore this email. "
            "The link expires after one hour."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


class PasswordResetRequestThrottle(AnonRateThrottle):
    rate = "5/hour"


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRequestThrottle]

    def post(self, request):
        identifier = request.data.get("identifier", "")
        if not isinstance(identifier, str) or not identifier.strip():
            return Response(
                {"detail": "Enter your registered email or student registration number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        identifier = identifier.strip()
        if "@" in identifier:
            user = User.objects.filter(
                email__iexact=identifier,
            ).exclude(user_type="student").first()
        else:
            profile = StudentProfile.objects.select_related("user").filter(
                registration_number=identifier
            ).first()
            user = profile.user if profile else None

        if user and user.is_active:
            try:
                send_password_reset_email(user)
            except Exception as error:
                # Keep account existence private and never log the token or address.
                logger.error(
                    "Password reset email delivery failed (%s).",
                    type(error).__name__,
                )

        return Response({
            "detail": (
                "If an active account matches those details, "
                "password reset instructions have been sent to its registered email."
            )
        })


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_user = serializer.validated_data["user"]
        with transaction.atomic():
            user = User.objects.select_for_update().filter(
                pk=validated_user.pk
            ).first()
            if user is None or not default_token_generator.check_token(
                user,
                serializer.validated_data["token"],
            ):
                logger.warning(
                    "password_reset_confirm token_check=false "
                    "reason=token_changed_before_password_save"
                )
                return Response(
                    {"detail": "This password reset link is invalid or expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data["new_password"])
            user.must_change_password = False
            user.save(update_fields=["password", "must_change_password", "updated_at"])
        return Response({"detail": "Password reset successfully. You can now sign in."})


class AdminPasswordResetView(generics.GenericAPIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            send_password_reset_email(user)
        except Exception as error:
            logger.error(
                "Admin-triggered password reset email delivery failed (%s).",
                type(error).__name__,
            )
            return Response(
                {"detail": "Unable to send the password reset email."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"detail": "Password reset email sent to the user's registered address."})


class AdminSetPasswordView(generics.GenericAPIView):
    serializer_class = AdminSetPasswordSerializer
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        user = User.objects.filter(pk=pk).first()
        if user is None:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "target_user": user},
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password", "updated_at"])
        return Response({"detail": "Password reset successfully."})
