from rest_framework import serializers

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


# =========================================================
# USER SERIALIZER
# =========================================================

class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "user_type",
            "phone_number",
            "profile_picture",
            "must_change_password",
            "is_active",
            "date_joined",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "date_joined",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        return instance

# =========================================================
# DEPARTMENT SERIALIZER
# =========================================================

class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "code",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


# =========================================================
# PROGRAM SERIALIZER
# =========================================================

class ProgramSerializer(serializers.ModelSerializer):

    department_name = serializers.CharField(
        source="department.name",
        read_only=True
    )

    class Meta:
        model = Program
        fields = [
            "id",
            "name",
            "code",
            "department",
            "department_name",
            "duration_years",
            "total_semesters",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "department_name",
            "created_at",
            "updated_at",
        ]


# =========================================================
# SEMESTER SERIALIZER
# =========================================================

class SemesterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Semester
        fields = [
            "id",
            "number",
            "title",
            "is_active",
        ]
        read_only_fields = [
            "id",
        ]


# =========================================================
# ACADEMIC SESSION SERIALIZER
# =========================================================

class AcademicSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = AcademicSession
        fields = [
            "id",
            "title",
            "session_type",
            "start_date",
            "end_date",
            "is_current",
        ]
        read_only_fields = [
            "id",
        ]


# =========================================================
# OFFICE SERIALIZER
# =========================================================

class OfficeSerializer(serializers.ModelSerializer):

    department_name = serializers.CharField(
        source="department.name",
        read_only=True
    )

    class Meta:
        model = Office
        fields = [
            "id",
            "name",
            "code",
            "department",
            "department_name",
            "office_location",
            "email",
            "contact_number",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "department_name",
            "created_at",
            "updated_at",
        ]


# =========================================================
# BATCH SERIALIZER
# =========================================================

class BatchSerializer(serializers.ModelSerializer):

    program_name = serializers.CharField(
        source="program.name",
        read_only=True
    )

    class Meta:
        model = Batch
        fields = [
            "id",
            "name",
            "program",
            "program_name",
            "admission_year",
            "graduation_year",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "program_name",
            "created_at",
            "updated_at",
        ]


# =========================================================
# STUDENT PROFILE SERIALIZER
# =========================================================

class StudentProfileSerializer(serializers.ModelSerializer):

    user_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True
    )

    program_name = serializers.CharField(
        source="program.name",
        read_only=True
    )

    batch_name = serializers.CharField(
        source="batch.name",
        read_only=True
    )

    semester_title = serializers.CharField(
        source="current_semester.title",
        read_only=True
    )

    academic_session_title = serializers.CharField(
        source="academic_session.title",
        read_only=True
    )

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user",
            "user_name",
            "registration_number",
            "program",
            "program_name",
            "batch",
            "batch_name",
            "current_semester",
            "semester_title",
            "academic_session",
            "academic_session_title",
            "cgpa",
            "date_of_birth",
            "gender",
            "address",
            "emergency_contact",
            "guardian_name",
            "guardian_phone",
            "is_active",
            "profile_completed",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "registration_number",
            "user_name",
            "program_name",
            "batch_name",
            "semester_title",
            "academic_session_title",
            "created_at",
            "updated_at",
        ]

    def validate_cgpa(self, value):

        if value < 0 or value > 4:
            raise serializers.ValidationError(
                "CGPA must be between 0.00 and 4.00."
            )

        return value


# =========================================================
# FACULTY PROFILE SERIALIZER
# =========================================================

class FacultyProfileSerializer(serializers.ModelSerializer):

    user_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True
    )

    department_name = serializers.CharField(
        source="department.name",
        read_only=True
    )

    office_name = serializers.CharField(
        source="office.name",
        read_only=True
    )

    class Meta:
        model = FacultyProfile
        fields = [
            "id",
            "user",
            "user_name",
            "employee_id",
            "department",
            "department_name",
            "designation",
            "specialization",
            "office",
            "office_name",
            "email_extension",
            "is_available_for_supervision",
            "max_fyp_groups",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user_name",
            "department_name",
            "office_name",
            "created_at",
            "updated_at",
        ]


# =========================================================
# STAFF PROFILE SERIALIZER
# =========================================================

class StaffProfileSerializer(serializers.ModelSerializer):

    user_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True
    )

    office_name = serializers.CharField(
        source="office.name",
        read_only=True
    )

    class Meta:
        model = StaffProfile
        fields = [
            "id",
            "user",
            "user_name",
            "employee_id",
            "office",
            "office_name",
            "designation",
            "joining_date",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user_name",
            "office_name",
            "created_at",
            "updated_at",
        ]


# =========================================================
# RESPONSIBILITY ASSIGNMENT SERIALIZER
# =========================================================

class ResponsibilityAssignmentSerializer(
    serializers.ModelSerializer
):

    faculty_name = serializers.CharField(
        source="faculty.user.get_full_name",
        read_only=True
    )

    staff_name = serializers.CharField(
        source="staff.user.get_full_name",
        read_only=True
    )

    department_name = serializers.CharField(
        source="department.name",
        read_only=True
    )

    office_name = serializers.CharField(
        source="office.name",
        read_only=True
    )

    batch_name = serializers.CharField(
        source="batch.name",
        read_only=True
    )

    class Meta:
        model = ResponsibilityAssignment

        fields = [
            "id",
            "faculty",
            "faculty_name",
            "staff",
            "staff_name",
            "department",
            "department_name",
            "office",
            "office_name",
            "batch",
            "batch_name",
            "responsibility_type",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "faculty_name",
            "staff_name",
            "department_name",
            "office_name",
            "batch_name",
            "created_at",
            "updated_at",
        ]

# =========================================================
# STUDENT LOGIN SERIALIZER
# =========================================================

class StudentLoginSerializer(serializers.Serializer):

    registration_number = serializers.CharField(
        required=True
    )

    password = serializers.CharField(
        required=True,
        write_only=True
    )

    def validate(self, attrs):

        registration_number = attrs.get("registration_number")
        password = attrs.get("password")

        try:
            student_profile = StudentProfile.objects.select_related(
                "user"
            ).get(
                registration_number=registration_number
            )
        except StudentProfile.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid registration number or password."
            )

        user = student_profile.user

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                "Invalid registration number or password."
            )

        if user.user_type != "student":
            raise serializers.ValidationError(
                "This account is not a student account."
            )

        attrs["user"] = user
        attrs["student_profile"] = student_profile

        return attrs