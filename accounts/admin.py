from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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


# =========================
# USER
# =========================

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "user_type",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Information",
            {
                "fields": (
                    "user_type",
                    "phone_number",
                    "profile_picture",
                    "must_change_password",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Additional Information",
            {
                "fields": (
                    "email",
                    "user_type",
                    "phone_number",
                    "profile_picture",
                    "must_change_password",
                )
            },
        ),
    )


# =========================
# DEPARTMENT
# =========================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "name",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "code",
    )


# =========================
# PROGRAM
# =========================

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "name",
        "department",
        "duration_years",
        "total_semesters",
        "is_active",
    )

    list_filter = (
        "department",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
    )


# =========================
# SEMESTER
# =========================

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):

    list_display = (
        "number",
        "title",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "title",
    )


# =========================
# ACADEMIC SESSION
# =========================

@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "session_type",
        "start_date",
        "end_date",
        "is_current",
    )

    list_filter = (
        "session_type",
        "is_current",
    )

    search_fields = (
        "title",
    )


# =========================
# OFFICE
# =========================

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "name",
        "department",
        "office_location",
        "email",
        "contact_number",
        "is_active",
    )

    list_filter = (
        "department",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "email",
    )


# =========================
# BATCH
# =========================

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "program",
        "admission_year",
        "graduation_year",
        "is_active",
    )

    list_filter = (
        "program",
        "is_active",
        "admission_year",
    )

    search_fields = (
        "name",
    )


# =========================
# STUDENT PROFILE
# =========================

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    list_display = (
        "registration_number",
        "user",
        "program",
        "batch",
        "current_semester",
        "academic_session",
        "cgpa",
        "profile_completed",
        "is_active",
    )

    list_filter = (
        "program",
        "batch",
        "current_semester",
        "academic_session",
        "gender",
        "profile_completed",
        "is_active",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )


# =========================
# FACULTY PROFILE
# =========================

@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):

    list_display = (
        "employee_id",
        "user",
        "department",
        "designation",
        "office",
        "is_available_for_supervision",
        "max_fyp_groups",
    )

    list_filter = (
        "department",
        "designation",
        "is_available_for_supervision",
    )

    search_fields = (
        "employee_id",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "specialization",
    )


# =========================
# STAFF PROFILE
# =========================

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):

    list_display = (
        "employee_id",
        "user",
        "office",
        "designation",
        "joining_date",
        "is_active",
    )

    list_filter = (
        "office",
        "designation",
        "is_active",
    )

    search_fields = (
        "employee_id",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )


# =========================
# RESPONSIBILITY ASSIGNMENT
# =========================

@admin.register(ResponsibilityAssignment)
class ResponsibilityAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        "responsibility_type",
        "faculty",
        "staff",
        "department",
        "office",
        "batch",
        "start_date",
        "end_date",
        "is_active",
    )

    list_filter = (
        "responsibility_type",
        "department",
        "office",
        "is_active",
    )

    search_fields = (
        "faculty__employee_id",
        "faculty__user__first_name",
        "faculty__user__last_name",
        "staff__employee_id",
        "staff__user__first_name",
        "staff__user__last_name",
    )