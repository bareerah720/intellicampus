from django.urls import path

from .views import (
    UserListCreateView,
    DepartmentListCreateView,
    ProgramListCreateView,
    SemesterListCreateView,
    AcademicSessionListCreateView,
    OfficeListCreateView,
    BatchListCreateView,
    StudentProfileListCreateView,
    FacultyProfileListCreateView,
    StaffProfileListCreateView,
    ResponsibilityAssignmentListCreateView,
)

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-list-create"),

    path(
        "departments/",
        DepartmentListCreateView.as_view(),
        name="department-list-create",
    ),

    path(
        "programs/",
        ProgramListCreateView.as_view(),
        name="program-list-create",
    ),

    path(
        "semesters/",
        SemesterListCreateView.as_view(),
        name="semester-list-create",
    ),

    path(
        "academic-sessions/",
        AcademicSessionListCreateView.as_view(),
        name="academic-session-list-create",
    ),

    path(
        "offices/",
        OfficeListCreateView.as_view(),
        name="office-list-create",
    ),

    path(
        "batches/",
        BatchListCreateView.as_view(),
        name="batch-list-create",
    ),

    path(
        "student-profiles/",
        StudentProfileListCreateView.as_view(),
        name="student-profile-list-create",
    ),

    path(
        "faculty-profiles/",
        FacultyProfileListCreateView.as_view(),
        name="faculty-profile-list-create",
    ),

    path(
        "staff-profiles/",
        StaffProfileListCreateView.as_view(),
        name="staff-profile-list-create",
    ),

    path(
        "responsibilities/",
        ResponsibilityAssignmentListCreateView.as_view(),
        name="responsibility-list-create",
    ),
]