from rest_framework import serializers

from django.contrib.auth.password_validation import (
    validate_password,
)

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.db.models import Q
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone

import logging

from .models import (
    User,
    UserType,
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

logger = logging.getLogger(__name__)


# =========================================================
# USER SERIALIZER
# =========================================================

class UserSerializer(serializers.ModelSerializer):

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
            "password",
            "user_type",
            "date_joined",
            "created_at",
            "updated_at",
            "must_change_password",
        ]

    def validate(self, attrs):

        submitted_email = self.initial_data.get("email")
        if (
            self.instance is not None
            and submitted_email is not None
            and submitted_email != self.instance.email
        ):
            raise serializers.ValidationError({
                "email": "University email addresses cannot be changed."
            })

        request = self.context.get("request")
        new_user_type = attrs.get(
            "user_type",
            self.instance.user_type if self.instance else None
        )

        if new_user_type == "admin" and (
            self.instance is None or self.instance.user_type != "admin"
        ):
            raise serializers.ValidationError({
                "user_type": "Central Admin is provisioned through the controlled account process."
            })

        # Only one Admin account is allowed.
        if (
            new_user_type == "admin"
            and User.objects.filter(user_type="admin").exclude(
                pk=self.instance.pk if self.instance else None
            ).exists()
        ):
            raise serializers.ValidationError({
                "user_type": "Only one central Admin account is allowed."
            })

        # Existing Admin cannot be converted to another role.
        if (
            self.instance
            and self.instance.user_type == "admin"
            and new_user_type != "admin"
        ):
            raise serializers.ValidationError({
                "user_type": "The central Admin role cannot be changed."
            })

        # Central Admin cannot be deactivated.
        if (
            self.instance
            and self.instance.user_type == "admin"
            and attrs.get("is_active") is False
        ):
            raise serializers.ValidationError({
                "is_active": "The central Admin account cannot be deactivated."
            })

        # Admin cannot deactivate their own account.
        if (
            request
            and request.user.is_authenticated
            and self.instance
            and self.instance.pk == request.user.pk
            and attrs.get("is_active") is False
        ):
            raise serializers.ValidationError({
                "is_active": "You cannot deactivate your own account."
            })

        return attrs

    def create(self, validated_data):
        raise serializers.ValidationError({
            "detail": "Controlled role-profile creation must use the admin-users endpoint."
        })

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

    total_semesters = serializers.IntegerField(
        read_only=True,
        help_text="Legacy stored value; not used to calculate the effective count.",
    )

    effective_semester_count = serializers.IntegerField(read_only=True)

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
            "semester_count_override",
            "semester_exception_approval_reference",
            "semester_exception_approval_note",
            "effective_semester_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "department_name",
            "total_semesters",
            "effective_semester_count",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        instance = self.instance
        candidate = Program(
            duration_years=attrs.get(
                "duration_years",
                instance.duration_years if instance else 4,
            ),
            semester_count_override=attrs.get(
                "semester_count_override",
                instance.semester_count_override if instance else None,
            ),
            semester_exception_approval_reference=attrs.get(
                "semester_exception_approval_reference",
                instance.semester_exception_approval_reference if instance else None,
            ),
            semester_exception_approval_note=attrs.get(
                "semester_exception_approval_note",
                instance.semester_exception_approval_note if instance else None,
            ),
        )
        try:
            candidate.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                getattr(error, "message_dict", error.messages)
            )
        return attrs


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

    def validate(self, attrs):
        instance = self.instance
        candidate = AcademicSession(
            pk=instance.pk if instance else None,
            title=attrs.get("title", instance.title if instance else ""),
            session_type=attrs.get(
                "session_type",
                instance.session_type if instance else "",
            ),
            start_date=attrs.get(
                "start_date",
                instance.start_date if instance else None,
            ),
            end_date=attrs.get(
                "end_date",
                instance.end_date if instance else None,
            ),
            is_current=attrs.get(
                "is_current",
                instance.is_current if instance else False,
            ),
        )
        try:
            candidate.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                getattr(error, "message_dict", error.messages)
            )
        return attrs


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

def validate_student_academic_relationships(instance, attrs, changed_fields):
    """Keep an edited student's program, cohort, term and registration coherent."""
    if not changed_fields:
        return

    errors = {}
    program = attrs.get("program", getattr(instance, "program", None))
    batch = attrs.get("batch", getattr(instance, "batch", None))
    semester = attrs.get(
        "current_semester",
        getattr(instance, "current_semester", None),
    )
    session = attrs.get(
        "academic_session",
        getattr(instance, "academic_session", None),
    )
    registration_number = attrs.get(
        "registration_number",
        getattr(instance, "registration_number", None),
    )

    if program and batch and batch.program_id != program.pk:
        errors["batch"] = "The selected batch does not belong to the selected program."

    if (
        batch
        and session
        and changed_fields
    ):
        expected_year = session.start_date.year
        expected_prefix = "Sp" if session.session_type == "spring" else "Fa"
        expected_batch_name = f"{expected_prefix}{expected_year % 100:02d}"
        if batch.admission_year != expected_year:
            errors["batch"] = "The batch admission year must match the admission session year."
        elif getattr(batch, "name", "").casefold() != expected_batch_name.casefold():
            errors["batch"] = "The batch season and name must match the admission session."

    if program and semester and semester.number > program.effective_semester_count:
        errors["current_semester"] = (
            "The semester is higher than this program's effective semester count."
        )

    if (
        program
        and session
        and registration_number
        and changed_fields.intersection(
            {"program", "academic_session", "registration_number"}
        )
    ):
        session_prefix = "SP" if session.session_type == "spring" else "FA"
        prefix = (
            f"{session_prefix}{session.start_date.year % 100:02d}-"
            f"{program.code.upper()}-"
        )
        suffix = registration_number[len(prefix):] if registration_number.startswith(prefix) else ""
        if not suffix.isdigit() or len(suffix) < 3:
            errors["registration_number"] = (
                "Registration number must use the admission session and program prefix."
            )

    if errors:
        raise serializers.ValidationError(errors)

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
            "guardian_phone",
            "is_active",
            "profile_completed",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user",
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

    def validate(self, attrs):
        request = self.context.get("request")
        is_admin = bool(
            request
            and request.user.is_authenticated
            and request.user.user_type == UserType.ADMIN
        )
        if not is_admin:
            editable_fields = {
                "date_of_birth",
                "gender",
                "address",
                "emergency_contact",
                "guardian_phone",
            }
            protected = set(self.initial_data) - editable_fields
            if protected:
                raise serializers.ValidationError({
                    field: "Only an administrator can change this field."
                    for field in protected
                })

        relationship_fields = {
            "program",
            "batch",
            "current_semester",
            "academic_session",
            "registration_number",
        }
        changed_fields = {
            field
            for field in relationship_fields
            if field in attrs
            and (self.instance is None or getattr(self.instance, field) != attrs[field])
        }
        if self.instance is None:
            changed_fields.update(relationship_fields - {"registration_number"})
        validate_student_academic_relationships(self.instance, attrs, changed_fields)

        submitted_registration_number = self.initial_data.get("registration_number")
        if not is_admin and submitted_registration_number is not None:
            raise serializers.ValidationError({
                "registration_number": "Student registration numbers cannot be changed."
            })
        if is_admin and submitted_registration_number:
            duplicate = StudentProfile.objects.filter(
                registration_number=submitted_registration_number,
            ).exclude(pk=getattr(self.instance, "pk", None)).exists()
            if duplicate:
                raise serializers.ValidationError({
                    "registration_number": "This registration number is already in use."
                })
        return attrs


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
            "address",
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
            "address",
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

class UserProfileSerializer(serializers.Serializer):
    """Expose self-service fields while keeping university identity data fixed."""

    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    user_type = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=20,
    )
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=StudentProfile.Gender.choices,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    emergency_contact = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=15,
    )
    guardian_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=15,
    )

    student_fields = {
        "date_of_birth",
        "gender",
        "address",
        "emergency_contact",
        "guardian_phone",
    }
    user_fields = {
        "phone_number",
        "profile_picture",
    }

    def is_admin_self(self):
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and request.user.pk == self.instance.pk
            and self.instance.user_type == UserType.ADMIN
        )

    def validate(self, attrs):
        submitted = self.initial_data
        allowed_fields = {"phone_number", "profile_picture"}
        if self.instance.user_type == UserType.STUDENT:
            allowed_fields.update(self.student_fields)
        elif self.instance.user_type in (UserType.FACULTY, UserType.STAFF):
            allowed_fields.add("address")
        if self.is_admin_self():
            allowed_fields.update({"first_name", "last_name"})
        forbidden_fields = set(submitted) - allowed_fields
        if forbidden_fields:
            raise serializers.ValidationError({
                field: "This field cannot be changed from profile settings."
                for field in forbidden_fields
            })

        phone_number = attrs.get("phone_number")
        if phone_number == "":
            attrs["phone_number"] = None
        elif phone_number:
            duplicate_phone = User.objects.filter(
                phone_number=phone_number,
            ).exclude(pk=self.instance.pk).exists()
            if duplicate_phone:
                raise serializers.ValidationError({
                    "phone_number": "This phone number is already in use."
                })

        return attrs

    def to_representation(self, user):
        image_field = self.fields["profile_picture"]
        role_profile = {}
        if user.user_type == UserType.STUDENT:
            role_profile = {
                "registration_number": None,
                "program": None,
                "batch": None,
                "current_semester": None,
                "admission_session": None,
                "cgpa": None,
                "date_of_birth": None,
                "gender": None,
                "address": None,
                "emergency_contact": None,
                "guardian_phone": None,
            }
        elif user.user_type == UserType.FACULTY:
            role_profile = {
                "employee_id": None,
                "department": None,
                "designation": None,
                "specialization": None,
                "office": None,
                "address": None,
            }
        elif user.user_type == UserType.STAFF:
            role_profile = {
                "employee_id": None,
                "office": None,
                "designation": None,
                "joining_date": None,
                "address": None,
            }
        result = {
            "id": user.pk,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "user_type": user.user_type,
            "phone_number": user.phone_number,
            "profile_picture": image_field.to_representation(user.profile_picture),
            "is_active": user.is_active,
            "role_profile": role_profile,
            "responsibilities": self._responsibilities(user),
        }

        if user.user_type == UserType.STUDENT:
            profile = StudentProfile.objects.select_related(
                "program",
                "batch",
                "current_semester",
                "academic_session",
            ).only(
                "id",
                "user_id",
                "registration_number",
                "cgpa",
                "date_of_birth",
                "gender",
                "address",
                "emergency_contact",
                "guardian_phone",
                "program__name",
                "batch__name",
                "current_semester__title",
                "academic_session__title",
            ).filter(user_id=user.pk).first()
            if profile:
                result["role_profile"] = {
                    "registration_number": profile.registration_number,
                    "program": profile.program.name,
                    "batch": profile.batch.name,
                    "current_semester": profile.current_semester.title,
                    "admission_session": profile.academic_session.title,
                    "cgpa": str(profile.cgpa),
                    "date_of_birth": self.fields["date_of_birth"].to_representation(
                        profile.date_of_birth
                    ),
                    "gender": profile.gender,
                    "address": profile.address,
                    "emergency_contact": profile.emergency_contact,
                    "guardian_phone": profile.guardian_phone,
                }
        elif user.user_type == UserType.FACULTY:
            profile = getattr(user, "faculty_profile", None)
            if profile:
                result["role_profile"] = {
                    "employee_id": profile.employee_id,
                    "department": profile.department.name,
                    "designation": profile.designation,
                    "address": profile.address,
                    "specialization": profile.specialization,
                    "office": profile.office.name if profile.office else None,
                    "email_extension": profile.email_extension,
                }
        elif user.user_type == UserType.STAFF:
            profile = getattr(user, "staff_profile", None)
            if profile:
                result["role_profile"] = {
                    "employee_id": profile.employee_id,
                    "office": profile.office.name,
                    "designation": profile.designation,
                    "address": profile.address,
                    "joining_date": profile.joining_date.isoformat()
                    if profile.joining_date
                    else None,
                }
        return result

    def _responsibilities(self, user):
        if user.user_type not in (UserType.FACULTY, UserType.STAFF):
            return []

        today = timezone.localdate()
        assignments = ResponsibilityAssignment.objects.filter(
            is_active=True,
            start_date__lte=today,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        if user.user_type == UserType.FACULTY:
            assignments = assignments.filter(faculty__user=user)
        else:
            assignments = assignments.filter(staff__user=user)

        assignments = assignments.select_related("department", "office", "batch")
        result = []
        for assignment in assignments:
            scopes = [
                value
                for value in (
                    assignment.department.name if assignment.department else None,
                    assignment.batch.name if assignment.batch else None,
                    assignment.office.name if assignment.office else None,
                )
                if value
            ]
            result.append({
                "type": assignment.responsibility_type,
                "label": assignment.get_responsibility_type_display(),
                "scope": ", ".join(scopes),
            })
        return result

    def update(self, user, validated_data):
        student_updates = {}
        if user.user_type == UserType.STUDENT:
            student_updates = {
                key: validated_data.pop(key)
                for key in tuple(validated_data)
                if key in self.student_fields
            }
        changed_user_fields = []
        editable_user_fields = set(self.user_fields)
        if self.is_admin_self():
            editable_user_fields.update({"first_name", "last_name"})
        for field in editable_user_fields:
            if field in validated_data:
                setattr(user, field, validated_data[field])
                changed_user_fields.append(field)

        if changed_user_fields:
            user.save(update_fields=[*changed_user_fields, "updated_at"])

        if student_updates:
            profile = getattr(user, "student_profile", None)
            if profile is None:
                raise serializers.ValidationError({
                    "profile": "Student profile is not available for this account."
                })
            for field, value in student_updates.items():
                setattr(profile, field, value)
            profile.save(update_fields=[*student_updates, "updated_at"])

        if user.user_type in (UserType.FACULTY, UserType.STAFF) and "address" in validated_data:
            profile_attr = "faculty_profile" if user.user_type == UserType.FACULTY else "staff_profile"
            profile = getattr(user, profile_attr, None)
            if profile is None:
                raise serializers.ValidationError({
                    "profile": "Employee profile is not available for this account."
                })
            profile.address = validated_data["address"]
            profile.save(update_fields=["address", "updated_at"])

        return user


class AdminUserManagementSerializer(serializers.Serializer):
    """Admin-only editor for existing account and role-profile fields."""

    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(required=False)
    user_type = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=20,
    )
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    registration_number = serializers.CharField(required=False, max_length=30)
    program = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(), required=False
    )
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(), required=False
    )
    current_semester = serializers.PrimaryKeyRelatedField(
        queryset=Semester.objects.all(), required=False
    )
    academic_session = serializers.PrimaryKeyRelatedField(
        queryset=AcademicSession.objects.all(), required=False
    )
    cgpa = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=False,
    )
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=StudentProfile.Gender.choices,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    emergency_contact = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=15
    )
    guardian_phone = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=15
    )

    employee_id = serializers.CharField(required=False, allow_blank=True, max_length=30)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), required=False
    )
    designation = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )
    specialization = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=255
    )
    office = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.all(), required=False, allow_null=True
    )
    email_extension = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=50
    )
    is_available_for_supervision = serializers.BooleanField(required=False)
    max_fyp_groups = serializers.IntegerField(required=False, min_value=1)
    joining_date = serializers.DateField(required=False, allow_null=True)
    staff_profile_is_active = serializers.BooleanField(required=False)

    common_fields = {
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "profile_picture",
    }
    role_fields = {
        UserType.STUDENT: {
            "registration_number",
            "program",
            "batch",
            "current_semester",
            "academic_session",
            "cgpa",
            "date_of_birth",
            "gender",
            "address",
            "emergency_contact",
            "guardian_phone",
        },
        UserType.FACULTY: {
            "employee_id",
            "department",
            "designation",
            "address",
            "specialization",
            "office",
            "email_extension",
            "is_available_for_supervision",
            "max_fyp_groups",
        },
        UserType.STAFF: {
            "employee_id",
            "office",
            "designation",
            "address",
            "joining_date",
            "staff_profile_is_active",
        },
    }

    def validate(self, attrs):
        user = self.instance
        submitted_role = self.initial_data.get("user_type")
        if submitted_role and submitted_role != user.user_type:
            raise serializers.ValidationError({
                "user_type": "Role changes must use a controlled account process."
            })

        allowed = self.common_fields | self.role_fields.get(user.user_type, set())
        unexpected = set(self.initial_data) - allowed - {"user_type"}
        if unexpected:
            raise serializers.ValidationError({
                field: "This field is not editable for this account type."
                for field in unexpected
            })

        email = attrs.get("email")
        if email:
            submitted_email = email.strip()
            request = self.context.get("request")
            is_admin_self = bool(
                user.user_type == UserType.ADMIN
                and request
                and request.user.is_authenticated
                and request.user.pk == user.pk
            )
            if is_admin_self and submitted_email != user.email:
                raise serializers.ValidationError({
                    "email": "The Central Admin university email cannot be changed from profile management."
                })
            email = user.email if is_admin_self else submitted_email.lower()
            attrs["email"] = email
            if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                raise serializers.ValidationError({
                    "email": "This email address is already in use."
                })
            if user.username.casefold() == user.email.casefold():
                if len(email) > User._meta.get_field("username").max_length:
                    raise serializers.ValidationError({
                        "email": "This email is too long to synchronize with the account username."
                    })
                if User.objects.exclude(pk=user.pk).filter(username=email).exists():
                    raise serializers.ValidationError({
                        "email": "This email conflicts with another account username."
                    })

        phone_number = attrs.get("phone_number")
        if phone_number == "":
            attrs["phone_number"] = None
        elif phone_number and User.objects.filter(
            phone_number=phone_number,
        ).exclude(pk=user.pk).exists():
            raise serializers.ValidationError({
                "phone_number": "This phone number is already in use."
            })

        if user.user_type == UserType.STUDENT:
            profile = getattr(user, "student_profile", None)
            if profile is None:
                raise serializers.ValidationError({
                    "profile": "The student profile is not available for editing."
                })
            registration_number = attrs.get("registration_number")
            if registration_number:
                duplicate = StudentProfile.objects.filter(
                    registration_number=registration_number,
                ).exclude(pk=profile.pk).exists()
                if duplicate:
                    raise serializers.ValidationError({
                        "registration_number": "This registration number is already in use."
                    })

            cgpa = attrs.get("cgpa")
            if cgpa is not None and not 0 <= cgpa <= 4:
                raise serializers.ValidationError({
                    "cgpa": "CGPA must be between 0.00 and 4.00."
                })

            academic_fields = {
                "registration_number",
                "program",
                "batch",
                "current_semester",
                "academic_session",
            }
            changed = {
                field
                for field in academic_fields
                if field in attrs and getattr(profile, field) != attrs[field]
            }
            validate_student_academic_relationships(profile, attrs, changed)

        elif user.user_type == UserType.FACULTY:
            profile = getattr(user, "faculty_profile", None)
            if profile is None:
                raise serializers.ValidationError({
                    "profile": "The faculty profile is not available for editing."
                })
            employee_id = attrs.get("employee_id")
            if "employee_id" in attrs and not employee_id:
                raise serializers.ValidationError({
                    "employee_id": "Faculty employee ID cannot be blank."
                })
            if employee_id and FacultyProfile.objects.filter(
                employee_id=employee_id,
            ).exclude(pk=profile.pk).exists():
                raise serializers.ValidationError({
                    "employee_id": "This employee ID is already in use."
                })
            if "department" in attrs and attrs["department"] is None:
                raise serializers.ValidationError({
                    "department": "Faculty must have a department."
                })
            if "designation" in attrs and not attrs["designation"].strip():
                raise serializers.ValidationError({
                    "designation": "Faculty designation cannot be blank."
                })

        elif user.user_type == UserType.STAFF:
            profile = getattr(user, "staff_profile", None)
            if profile is None:
                raise serializers.ValidationError({
                    "profile": "The staff profile is not available for editing."
                })
            employee_id = attrs.get("employee_id")
            if "employee_id" in attrs and not employee_id:
                raise serializers.ValidationError({
                    "employee_id": "Staff employee ID cannot be blank."
                })
            if employee_id and StaffProfile.objects.filter(
                employee_id=employee_id,
            ).exclude(pk=profile.pk).exists():
                raise serializers.ValidationError({
                    "employee_id": "This employee ID is already in use."
                })
            if "office" in attrs and attrs["office"] is None:
                raise serializers.ValidationError({
                    "office": "Staff must have an office."
                })
            if "designation" in attrs and not attrs["designation"].strip():
                raise serializers.ValidationError({
                    "designation": "Staff designation cannot be blank."
                })

        return attrs

    def to_representation(self, user):
        result = {
            "id": user.pk,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "user_type": user.user_type,
            "phone_number": user.phone_number,
            "profile_picture": self.fields["profile_picture"].to_representation(
                user.profile_picture
            ),
            "is_active": user.is_active,
            "role_profile": {},
            "responsibilities": UserProfileSerializer(context=self.context)._responsibilities(user),
        }

        if user.user_type == UserType.STUDENT:
            profile = StudentProfile.objects.select_related(
                "program", "batch", "current_semester", "academic_session"
            ).only(
                "id", "user_id", "registration_number", "cgpa", "date_of_birth",
                "gender", "address", "emergency_contact",
                "guardian_phone", "program__name", "batch__name",
                "current_semester__title", "current_semester__number",
                "academic_session__title", "academic_session__session_type",
                "academic_session__start_date",
            ).filter(user_id=user.pk).first()
            if profile:
                result["role_profile"] = {
                    "id": profile.pk,
                    "registration_number": profile.registration_number,
                    "program": profile.program_id,
                    "program_name": profile.program.name,
                    "batch": profile.batch_id,
                    "batch_name": profile.batch.name,
                    "current_semester": profile.current_semester_id,
                    "current_semester_title": profile.current_semester.title,
                    "current_semester_number": profile.current_semester.number,
                    "academic_session": profile.academic_session_id,
                    "admission_session": profile.academic_session.title,
                    "cgpa": str(profile.cgpa) if profile.cgpa is not None else None,
                    "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                    "gender": profile.gender,
                    "address": profile.address,
                    "emergency_contact": profile.emergency_contact,
                    "guardian_phone": profile.guardian_phone,
                }
        elif user.user_type == UserType.FACULTY:
            profile = getattr(user, "faculty_profile", None)
            if profile:
                result["role_profile"] = {
                    "id": profile.pk,
                    "employee_id": profile.employee_id,
                    "department": profile.department_id,
                    "department_name": profile.department.name,
                    "designation": profile.designation,
                    "address": profile.address,
                    "specialization": profile.specialization,
                    "office": profile.office_id,
                    "office_name": profile.office.name if profile.office else None,
                    "email_extension": profile.email_extension,
                    "is_available_for_supervision": profile.is_available_for_supervision,
                    "max_fyp_groups": profile.max_fyp_groups,
                }
        elif user.user_type == UserType.STAFF:
            profile = getattr(user, "staff_profile", None)
            if profile:
                result["role_profile"] = {
                    "id": profile.pk,
                    "employee_id": profile.employee_id,
                    "office": profile.office_id,
                    "office_name": profile.office.name,
                    "designation": profile.designation,
                    "address": profile.address,
                    "joining_date": profile.joining_date.isoformat() if profile.joining_date else None,
                    "staff_profile_is_active": profile.is_active,
                }
        return result

    def update(self, user, validated_data):
        profile_fields_by_role = {
            UserType.STUDENT: {
                "registration_number", "program", "batch", "current_semester",
                "academic_session", "cgpa", "date_of_birth", "gender", "address",
                "emergency_contact", "guardian_phone",
            },
            UserType.FACULTY: {
                "employee_id", "department", "designation", "address", "specialization",
                "office", "email_extension", "is_available_for_supervision",
                "max_fyp_groups",
            },
            UserType.STAFF: {
                "employee_id", "office", "designation", "address", "joining_date",
                "staff_profile_is_active",
            },
        }
        profile_fields = profile_fields_by_role.get(user.user_type, set())
        role_updates = {
            key: validated_data.pop(key)
            for key in tuple(validated_data)
            if key in profile_fields
        }
        old_email = user.email
        user_updates = []
        for field, value in validated_data.items():
            setattr(user, field, value)
            user_updates.append(field)
        if user.email != old_email and user.username.casefold() == old_email.casefold():
            user.username = user.email
            user_updates.append("username")
        if user_updates:
            user.save(update_fields=[*user_updates, "updated_at"])

        if role_updates:
            profile = getattr(
                user,
                {
                    UserType.STUDENT: "student_profile",
                    UserType.FACULTY: "faculty_profile",
                    UserType.STAFF: "staff_profile",
                }[user.user_type],
                None,
            )
            if profile is None:
                raise serializers.ValidationError({
                    "profile": "The role profile is not available for editing."
                })
            if user.user_type == UserType.STAFF and "staff_profile_is_active" in role_updates:
                role_updates["is_active"] = role_updates.pop("staff_profile_is_active")
            for field, value in role_updates.items():
                setattr(profile, field, value)
            profile.save(update_fields=[*role_updates, "updated_at"])
        return user


class AdminSetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        forbidden_fields = {
            field: "This endpoint only changes passwords."
            for field in ("email", "registration_number")
            if field in self.initial_data
        }
        if forbidden_fields:
            raise serializers.ValidationError(forbidden_fields)

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "The passwords do not match."
            })

        try:
            validate_password(
                attrs["new_password"],
                user=self.context["target_user"],
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                "new_password": error.messages
            })
        return attrs


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

        if not student_profile.is_active:
            raise serializers.ValidationError(
                "This student profile is inactive."
            )

        attrs["user"] = user
        attrs["student_profile"] = student_profile

        return attrs

class ChangePasswordSerializer(
    serializers.Serializer
):

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        trim_whitespace=False,
    )

    new_password = serializers.CharField(
        required=True,
        write_only=True,
        trim_whitespace=False,
    )

    def validate_current_password(self, value):

        user = self.context["request"].user

        if not user.check_password(value):

            raise serializers.ValidationError(
                "Current password is incorrect."
            )

        return value

    def validate_new_password(self, value):

        user = self.context["request"].user

        try:

            validate_password(
                value,
                user=user
            )

        except DjangoValidationError as error:

            raise serializers.ValidationError(
                error.messages
            )

        return value

    def validate(self, attrs):

        if (
            attrs["current_password"]
            == attrs["new_password"]
        ):

            raise serializers.ValidationError(
                {
                    "new_password":
                    "New password must be different."
                }
            )

        return attrs
# =========================================================
# EMAIL LOGIN SERIALIZER
# =========================================================

class EmailLoginSerializer(serializers.Serializer):

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):

        email = attrs.get("email", "").strip()
        password = attrs.get("password")

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if (
            not user
            or not user.is_active
            or user.user_type == "student"
            or not user.check_password(password)
        ):
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        attrs["user"] = user
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        from django.contrib.auth.tokens import default_token_generator

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "The passwords do not match."
            })

        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
        except (TypeError, ValueError, OverflowError):
            logger.warning(
                "password_reset_confirm uid_decoded=false "
                "user_lookup=not_attempted token_check=not_run "
                "reason=uid_decode_failed"
            )
            raise serializers.ValidationError({
                "detail": "This password reset link is invalid or expired."
            })

        try:
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            logger.warning(
                "password_reset_confirm uid_decoded=true "
                "user_lookup=false token_check=not_run "
                "reason=user_not_found"
            )
            raise serializers.ValidationError({
                "detail": "This password reset link is invalid or expired."
            })

        token_valid = default_token_generator.check_token(user, attrs["token"])
        if not token_valid:
            logger.warning(
                "password_reset_confirm uid_decoded=true "
                "user_lookup=true token_check=false "
                "reason=token_invalid_or_expired"
            )
            raise serializers.ValidationError({
                "detail": "This password reset link is invalid or expired."
            })

        logger.info(
            "password_reset_confirm uid_decoded=true "
            "user_lookup=true token_check=true reason=none"
        )

        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                "new_password": error.messages
            })

        attrs["user"] = user
        return attrs


# =========================================================
# ADMIN USER + ROLE PROFILE CREATION
# =========================================================

from django.db import transaction


class AdminUserCreateSerializer(serializers.Serializer):

    # Common user fields

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    user_type = serializers.ChoiceField(
        choices=User._meta.get_field("user_type").choices
    )
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    # Student profile fields
    program = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(),
        required=False
    )
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(),
        required=False
    )
    current_semester = serializers.PrimaryKeyRelatedField(
        queryset=Semester.objects.all(),
        required=False
    )
    academic_session = serializers.PrimaryKeyRelatedField(
        queryset=AcademicSession.objects.all(),
        required=False
    )

    # Faculty profile fields
    employee_id = serializers.CharField(
        max_length=30,
        required=False
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=False
    )
    designation = serializers.CharField(
        max_length=100,
        required=False
    )
    specialization = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )
    office = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.all(),
        required=False,
        allow_null=True
    )

    def validate(self, attrs):

        user_type = attrs["user_type"]

        if user_type == "admin":
            raise serializers.ValidationError({
                "user_type": "Central Admin is provisioned through the controlled account process."
            })

        if User.objects.filter(
            username__iexact=attrs["email"].strip()
        ).exists():
            raise serializers.ValidationError({
                "email": "This email is already being used as a username."
            })

        if User.objects.filter(
            email__iexact=attrs["email"]
        ).exists():
            raise serializers.ValidationError({
                "email": "This email is already in use."
            })

        if user_type == "student":
            required = [
                "program",
                "batch",
                "current_semester",
                "academic_session",
            ]

            missing = [
                field for field in required
                if field not in attrs
            ]

            if missing:
                raise serializers.ValidationError({
                    field: "This field is required for students."
                    for field in missing
                })

        if user_type == "faculty":
            required = [
                "employee_id",
                "department",
                "designation",
            ]

            missing = [
                field for field in required
                if not attrs.get(field)
            ]

            if missing:
                raise serializers.ValidationError({
                    field: "This field is required for faculty."
                    for field in missing
                })

        if user_type == "staff":
            required = [
                "employee_id",
                "office",
                "designation",
            ]

            missing = [
                field for field in required
                if not attrs.get(field)
            ]

            if missing:
                raise serializers.ValidationError({
                    field: "This field is required for staff."
                    for field in missing
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        user_type = validated_data["user_type"]

        profile_fields = {
            "program",
            "batch",
            "current_semester",
            "academic_session",
            "employee_id",
            "department",
            "designation",
            "specialization",
            "office",
        }

        profile_data = {
            key: validated_data.pop(key)
            for key in list(validated_data.keys())
            if key in profile_fields
        }

        password = validated_data.pop("password")

        email = validated_data["email"].strip().lower()
        validated_data["email"] = email
        validated_data["username"] = email

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if user_type == "student":
            StudentProfile.objects.create(
                user=user,
                **profile_data
            )

        elif user_type == "faculty":
            FacultyProfile.objects.create(
                user=user,
                **profile_data
            )

        elif user_type == "staff":
            StaffProfile.objects.create(
                user=user,
                **profile_data
            )

        return user
