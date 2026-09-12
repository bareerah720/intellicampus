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
)


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
    StudentProfileSerializer,
    FacultyProfileSerializer,
    StaffProfileSerializer,
    ResponsibilityAssignmentSerializer,
    StudentLoginSerializer,
)

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]


class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class ProgramListCreateView(generics.ListCreateAPIView):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]

class ProgramDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]


class SemesterListCreateView(generics.ListCreateAPIView):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated]

class SemesterDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated]


class AcademicSessionListCreateView(generics.ListCreateAPIView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsAuthenticated]

class AcademicSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsAuthenticated]


class OfficeListCreateView(generics.ListCreateAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated]

class OfficeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated]


class BatchListCreateView(generics.ListCreateAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]

class BatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]


class StudentProfileListCreateView(generics.ListCreateAPIView):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAdminOrStudent]

class StudentProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAdminOrStudent, IsOwnerOrAdmin]


class FacultyProfileListCreateView(generics.ListCreateAPIView):
    queryset = FacultyProfile.objects.all()
    serializer_class = FacultyProfileSerializer
    permission_classes = [IsAdminOrFaculty]

class FacultyProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FacultyProfile.objects.all()
    serializer_class = FacultyProfileSerializer
    permission_classes = [IsAdminOrFaculty, IsOwnerOrAdmin]


class StaffProfileListCreateView(generics.ListCreateAPIView):
    queryset = StaffProfile.objects.all()
    serializer_class = StaffProfileSerializer
    permission_classes = [IsAdminOrStaff]


class StaffProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StaffProfile.objects.all()
    serializer_class = StaffProfileSerializer
    permission_classes = [IsAdminOrStaff, IsOwnerOrAdmin]


class ResponsibilityAssignmentListCreateView(generics.ListCreateAPIView):
    queryset = ResponsibilityAssignment.objects.all()
    serializer_class = ResponsibilityAssignmentSerializer
    permission_classes = [IsAdminOrFaculty]

class ResponsibilityAssignmentDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = ResponsibilityAssignment.objects.all()
    serializer_class = ResponsibilityAssignmentSerializer
    permission_classes = [IsAdminOrFaculty]

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