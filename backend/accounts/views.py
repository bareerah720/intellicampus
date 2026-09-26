from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
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
)

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
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]


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

# =========================================================
# STUDENT LOGIN VIEW
# =========================================================

class StudentLoginView(generics.GenericAPIView):

    serializer_class = StudentLoginSerializer
    permission_classes = [AllowAny]

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