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
    AdminUserCreateView,
    UserDetailView,
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
    StudentLoginView,
    EmailLoginView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    AdminPasswordResetView,
    AdminUserProfileView,
    AdminUserManagementView,
    AdminSetPasswordView,
    MyProfileView,
)

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
    path("admin-users/", AdminUserCreateView.as_view(), name="admin-user-create"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path(
        "users/<int:pk>/profile/",
        AdminUserProfileView.as_view(),
        name="admin-user-profile",
    ),
    path(
        "users/<int:pk>/management-profile/",
        AdminUserManagementView.as_view(),
        name="admin-user-management-profile",
    ),
    path(
        "users/<int:pk>/set-password/",
        AdminSetPasswordView.as_view(),
        name="admin-user-set-password",
    ),
    path(
        "users/<int:pk>/password-reset/",
        AdminPasswordResetView.as_view(),
        name="admin-user-password-reset",
    ),

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
    path(
        "me/profile/",
        MyProfileView.as_view(),
        name="my-profile",
    ),



    path(
        "email-login/",
        EmailLoginView.as_view(),
        name="email-login",
    ),
    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),

    path(
    "student-login/",
    StudentLoginView.as_view(),
    name="student-login",
),

    path(
    "change-password/",
    ChangePasswordView.as_view(),
    name="change-password",
),

]
