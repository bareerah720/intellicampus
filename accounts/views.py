from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

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
)


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class ProgramListCreateView(generics.ListCreateAPIView):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]


class SemesterListCreateView(generics.ListCreateAPIView):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated]


class AcademicSessionListCreateView(generics.ListCreateAPIView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsAuthenticated]


class OfficeListCreateView(generics.ListCreateAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsAuthenticated]


class BatchListCreateView(generics.ListCreateAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]


class StudentProfileListCreateView(generics.ListCreateAPIView):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]


class FacultyProfileListCreateView(generics.ListCreateAPIView):
    queryset = FacultyProfile.objects.all()
    serializer_class = FacultyProfileSerializer
    permission_classes = [IsAuthenticated]


class StaffProfileListCreateView(generics.ListCreateAPIView):
    queryset = StaffProfile.objects.all()
    serializer_class = StaffProfileSerializer
    permission_classes = [IsAuthenticated]


class ResponsibilityAssignmentListCreateView(generics.ListCreateAPIView):
    queryset = ResponsibilityAssignment.objects.all()
    serializer_class = ResponsibilityAssignmentSerializer
    permission_classes = [IsAuthenticated]