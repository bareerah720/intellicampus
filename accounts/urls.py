from django.urls import path

from .views import (
    AcademicSessionDetailView,
    BatchDetailView,
    CurrentUserView,
    DepartmentDetailView,
    FacultyProfileDetailView,
    OfficeDetailView,
    ProgramDetailView,
    ResponsibilityAssignmentDetailView,
    SemesterDetailView,
    StaffProfileDetailView,
    StudentProfileDetailView,
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
        "departments/<int:pk>/",
        DepartmentDetailView.as_view(),
        name="department-detail",
),

    path(
        "programs/",
        ProgramListCreateView.as_view(),
        name="program-list-create",
    ),

    path(
        "programs/<int:pk>/",
        ProgramDetailView.as_view(),
        name="program-detail",
    ),

    path(
        "semesters/",
        SemesterListCreateView.as_view(),
        name="semester-list-create",
    ),

    path(
        "semesters/<int:pk>/",
        SemesterDetailView.as_view(),
        name="semester-detail",
   ),

    path(
        "academic-sessions/",
        AcademicSessionListCreateView.as_view(),
        name="academic-session-list-create",
    ),

    path(
       "academic-sessions/<int:pk>/",
       AcademicSessionDetailView.as_view(),
       name="academic-session-detail",
    ),

    path(
        "offices/",
        OfficeListCreateView.as_view(),
        name="office-list-create",
    ),

    path(
       "offices/<int:pk>/",
       OfficeDetailView.as_view(),
       name="office-detail",
    ),

    path(
        "batches/",
        BatchListCreateView.as_view(),
        name="batch-list-create",
    ),

    path(
       "batches/<int:pk>/",
       BatchDetailView.as_view(),
       name="batch-detail",
    ),

    path(
        "student-profiles/",
        StudentProfileListCreateView.as_view(),
        name="student-profile-list-create",
    ),

    path(
    "student-profiles/<int:pk>/",
    StudentProfileDetailView.as_view(),
    name="student-profile-detail",
),

    path(
        "faculty-profiles/",
        FacultyProfileListCreateView.as_view(),
        name="faculty-profile-list-create",
    ),

    path(
    "faculty-profiles/<int:pk>/",
    FacultyProfileDetailView.as_view(),
    name="faculty-profile-detail",
),

    path(
        "staff-profiles/",
        StaffProfileListCreateView.as_view(),
        name="staff-profile-list-create",
    ),

    path(
    "staff-profiles/<int:pk>/",
    StaffProfileDetailView.as_view(),
    name="staff-profile-detail",
),

    path(
        "responsibilities/",
        ResponsibilityAssignmentListCreateView.as_view(),
        name="responsibility-list-create",
    ),

    path(
    "responsibilities/<int:pk>/",
    ResponsibilityAssignmentDetailView.as_view(),
    name="responsibility-detail",
),

    path(
    "me/",
    CurrentUserView.as_view(),
    name="current-user",
),
]