from contextlib import nullcontext
from datetime import date
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from PIL import Image
from rest_framework import serializers
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from accounts.models import (
    AcademicSession,
    Batch,
    Department,
    FacultyProfile,
    Office,
    Program,
    Semester,
    StaffProfile,
    StudentProfile,
    User,
    UserType,
)
from accounts.permissions import IsAdmin
from accounts.serializers import (
    AdminSetPasswordSerializer,
    AdminUserManagementSerializer,
    EmailLoginSerializer,
    PasswordResetConfirmSerializer,
    StudentLoginSerializer,
    StudentProfileSerializer,
    UserSerializer,
    UserProfileSerializer,
    validate_student_academic_relationships,
)
from accounts.views import (
    AdminUserManagementView,
    AdminSetPasswordView,
    ChangePasswordView,
    EmailLoginView,
    FacultyProfileDetailView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    StudentLoginView,
    StaffProfileDetailView,
    send_password_reset_email,
)


class EmailLoginPasswordWhitespaceTests(SimpleTestCase):
    def test_password_whitespace_is_preserved_for_verification(self):
        submitted_password = "  password with surrounding whitespace  "
        user = Mock(is_active=True, user_type="admin")
        user.check_password.return_value = True

        with patch("accounts.serializers.User.objects.filter") as user_filter:
            user_filter.return_value.first.return_value = user
            serializer = EmailLoginSerializer(data={
                "email": "admin@example.edu",
                "password": submitted_password,
            })

            self.assertTrue(serializer.is_valid(), serializer.errors)

        user.check_password.assert_called_once_with(submitted_password)


class ProfileAndPasswordSafetyTests(SimpleTestCase):
    def test_profile_api_rejects_email_and_registration_number_changes(self):
        student = User(
            id=17,
            username="student-17",
            email="student17@example.edu",
            user_type=UserType.STUDENT,
        )
        for field, value in (
            ("email", "changed@example.edu"),
            ("registration_number", "NEW-REG-17"),
        ):
            with self.subTest(field=field):
                serializer = UserProfileSerializer(
                    instance=student,
                    data={field: value},
                    partial=True,
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_student_profile_api_rejects_registration_number_change(self):
        serializer = StudentProfileSerializer(
            instance=StudentProfile(pk=17, registration_number="OLD-REG-17"),
            data={"registration_number": "NEW-REG-17"},
            partial=True,
        )
        unique_validator = next(
            validator
            for validator in serializer.fields["registration_number"].validators
            if hasattr(validator, "queryset")
        )
        unique_validator.queryset = Mock()
        unique_validator.queryset.exclude.return_value.filter.return_value.exists.return_value = False
        self.assertFalse(serializer.is_valid())
        self.assertIn("registration_number", serializer.errors)


class ProfileManagementPermissionTests(SimpleTestCase):
    def setUp(self):
        self.student = User(
            id=71,
            username="student-71",
            email="student71@example.edu",
            user_type=UserType.STUDENT,
        )

    def test_student_profile_endpoint_rejects_all_university_managed_fields(self):
        academic_fields = (
            "first_name",
            "last_name",
            "email",
            "registration_number",
            "program",
            "batch",
            "current_semester",
            "academic_session",
            "cgpa",
            "guardian_name",
        )
        for field in academic_fields:
            with self.subTest(field=field):
                serializer = UserProfileSerializer(
                    instance=self.student,
                    data={field: "changed"},
                    partial=True,
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_student_profile_endpoint_accepts_only_permitted_personal_fields(self):
        for field, value in (
            ("date_of_birth", "2004-01-02"),
            ("gender", "female"),
            ("address", "New address"),
            ("emergency_contact", "03001234567"),
            ("guardian_phone", "03007654321"),
        ):
            with self.subTest(field=field):
                serializer = UserProfileSerializer(
                    instance=self.student,
                    data={field: value},
                    partial=True,
                )
                self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_student_profile_model_endpoint_rejects_guardian_name_and_academics(self):
        profile = StudentProfile(registration_number="SP23-CS-0071")
        for field, value in (
            ("guardian_name", "Changed guardian"),
            ("program", "1"),
            ("batch", "1"),
            ("current_semester", "1"),
            ("academic_session", "1"),
            ("cgpa", "4.00"),
        ):
            with self.subTest(field=field):
                serializer = StudentProfileSerializer(
                    instance=profile,
                    data={field: value},
                    partial=True,
                )
                if field in {"program", "batch", "current_semester", "academic_session"}:
                    relation = SimpleNamespace(pk=1, number=1)
                    queryset = Mock()
                    queryset.get.return_value = relation
                    serializer.fields[field].queryset = queryset
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_non_student_self_profiles_reject_student_identifiers(self):
        for role in (UserType.FACULTY, UserType.STAFF, UserType.ADMIN):
            account = User(
                id=72,
                username=f"{role}-72",
                email=f"{role}-72@example.edu",
                user_type=role,
            )
            for field in ("email", "registration_number", "guardian_name"):
                with self.subTest(role=role, field=field):
                    serializer = UserProfileSerializer(
                        instance=account,
                        data={field: "must not be accepted"},
                        partial=True,
                    )
                    self.assertFalse(serializer.is_valid())
                    self.assertIn(field, serializer.errors)

    def test_admin_can_edit_student_identity_and_academic_fields(self):
        program = Program(id=4, code="CS", name="Computer Science", duration_years=4)
        session = AcademicSession(
            id=5,
            title="Spring 2023",
            session_type="spring",
            start_date=date(2023, 2, 1),
            end_date=date(2023, 7, 31),
        )
        batch = Batch(id=6, name="Sp23", program=program, admission_year=2023)
        semester = Semester(id=1, number=1, title="Semester 1")
        profile = StudentProfile(
            id=7,
            registration_number="SP23-CS-0071",
            program=program,
            batch=batch,
            current_semester=semester,
            academic_session=session,
            cgpa="3.25",
        )
        account = User(
            id=71,
            username="student71@example.edu",
            email="student71@example.edu",
            user_type=UserType.STUDENT,
        )
        account._state.fields_cache["student_profile"] = profile
        profile.user = account
        filters = Mock()
        filters.exclude.return_value = filters
        filters.exists.return_value = False
        filters.filter.return_value.exists.return_value = False
        student_filters = Mock()
        student_filters.exclude.return_value = student_filters
        student_filters.exists.return_value = False
        payload = {
            "first_name": "Updated",
            "email": "updated71@example.edu",
            "registration_number": "SP23-CS-1071",
            "program": program.pk,
            "batch": batch.pk,
            "current_semester": semester.pk,
            "academic_session": session.pk,
            "cgpa": "3.80",
            "address": "Updated address",
        }
        with (
            patch("accounts.serializers.User.objects.filter", return_value=filters),
            patch("accounts.serializers.User.objects.exclude", return_value=filters),
            patch("accounts.serializers.StudentProfile.objects.filter", return_value=student_filters),
        ):
            serializer = AdminUserManagementSerializer(
                instance=account,
                data=payload,
                partial=True,
            )
            for field, relation in (
                ("program", program),
                ("batch", batch),
                ("current_semester", semester),
                ("academic_session", session),
            ):
                queryset = Mock()
                queryset.get.return_value = relation
                serializer.fields[field].queryset = queryset
            self.assertTrue(serializer.is_valid(), serializer.errors)

        account.save = Mock()
        profile.save = Mock()
        serializer.save()
        self.assertEqual(account.first_name, "Updated")
        self.assertEqual(account.email, "updated71@example.edu")
        self.assertEqual(account.username, "updated71@example.edu")
        self.assertEqual(profile.registration_number, "SP23-CS-1071")
        self.assertEqual(str(profile.cgpa), "3.80")
        self.assertEqual(profile.address, "Updated address")
        account.save.assert_called_once()
        profile.save.assert_called_once()

    def test_student_academic_relationship_validation_rejects_program_batch_mismatch(self):
        program = SimpleNamespace(pk=1, effective_semester_count=8, code="CS")
        other_program = SimpleNamespace(pk=2, code="EE")
        batch = SimpleNamespace(program_id=other_program.pk, admission_year=2023)
        semester = SimpleNamespace(number=1)
        session = SimpleNamespace(
            session_type="spring",
            start_date=SimpleNamespace(year=2023),
        )
        with self.assertRaises(serializers.ValidationError):
            validate_student_academic_relationships(
                None,
                {
                    "program": program,
                    "batch": batch,
                    "current_semester": semester,
                    "academic_session": session,
                    "registration_number": "SP23-CS-0001",
                },
                {"program", "batch"},
            )

    def test_student_academic_relationship_validation_rejects_wrong_year_and_semester(self):
        program = SimpleNamespace(pk=1, effective_semester_count=4, code="CS")
        batch = SimpleNamespace(program_id=1, admission_year=2024)
        semester = SimpleNamespace(number=5)
        session = SimpleNamespace(
            session_type="spring",
            start_date=SimpleNamespace(year=2023),
        )
        with self.assertRaises(serializers.ValidationError) as error:
            validate_student_academic_relationships(
                None,
                {
                    "program": program,
                    "batch": batch,
                    "current_semester": semester,
                    "academic_session": session,
                    "registration_number": "FA23-CS-0001",
                },
                {"academic_session", "current_semester", "registration_number"},
            )
        self.assertIn("batch", error.exception.detail)
        self.assertIn("current_semester", error.exception.detail)
        self.assertIn("registration_number", error.exception.detail)

    def test_student_batch_season_must_match_admission_session(self):
        program = SimpleNamespace(pk=1, effective_semester_count=8, code="CS")
        batch = SimpleNamespace(program_id=1, admission_year=2023, name="Fa23")
        session = SimpleNamespace(
            session_type="spring",
            start_date=SimpleNamespace(year=2023),
        )
        with self.assertRaises(serializers.ValidationError) as error:
            validate_student_academic_relationships(
                None,
                {
                    "program": program,
                    "batch": batch,
                    "current_semester": SimpleNamespace(number=1),
                    "academic_session": session,
                    "registration_number": "SP23-CS-0001",
                },
                {"batch"},
            )
        self.assertIn("batch", error.exception.detail)

    def test_admin_profile_editor_updates_faculty_and_staff_model_fields(self):
        department = Department(id=3, name="Computing", code="CS")
        office = Office(id=4, name="Main Office", code="MO", department=department)
        faculty_user = User(
            id=73,
            username="faculty73",
            email="faculty73@example.edu",
            user_type=UserType.FACULTY,
        )
        faculty = FacultyProfile(
            id=8,
            user=faculty_user,
            employee_id="FAC-73",
            department=department,
            designation="Lecturer",
        )
        faculty_user._state.fields_cache["faculty_profile"] = faculty
        faculty.save = Mock()
        faculty_user.save = Mock()
        AdminUserManagementSerializer(instance=faculty_user).update(faculty_user, {
            "employee_id": "FAC-73A",
            "department": department,
            "designation": "Senior Lecturer",
            "office": office,
            "specialization": "Networks",
            "email_extension": "1234",
            "is_available_for_supervision": False,
            "max_fyp_groups": 3,
        })
        self.assertEqual(faculty.employee_id, "FAC-73A")
        self.assertEqual(faculty.designation, "Senior Lecturer")
        self.assertEqual(faculty.office, office)
        self.assertEqual(faculty.max_fyp_groups, 3)
        faculty.save.assert_called_once()

        staff_user = User(
            id=74,
            username="staff74",
            email="staff74@example.edu",
            user_type=UserType.STAFF,
        )
        staff = StaffProfile(
            id=9,
            user=staff_user,
            employee_id="STF-74",
            office=office,
            designation="Coordinator",
        )
        staff_user._state.fields_cache["staff_profile"] = staff
        staff.save = Mock()
        staff_user.save = Mock()
        AdminUserManagementSerializer(instance=staff_user).update(staff_user, {
            "employee_id": "STF-74A",
            "office": office,
            "designation": "Senior Coordinator",
            "joining_date": date(2020, 1, 2),
            "staff_profile_is_active": False,
        })
        self.assertEqual(staff.employee_id, "STF-74A")
        self.assertEqual(staff.designation, "Senior Coordinator")
        self.assertEqual(staff.joining_date, date(2020, 1, 2))
        self.assertFalse(staff.is_active)
        staff.save.assert_called_once()

    def test_non_admin_cannot_access_admin_profile_editor(self):
        request = APIRequestFactory().patch("/api/accounts/users/75/management-profile/")
        force_authenticate(
            request,
            user=User(id=75, username="student75", user_type=UserType.STUDENT),
        )
        response = AdminUserManagementView.as_view()(request, pk=75)
        self.assertEqual(response.status_code, 403)

    def test_employee_self_profile_can_save_address_but_not_employee_id(self):
        department = Department(id=13, name="Computing", code="CS")
        office = Office(id=14, name="Main Office", code="MO", department=department)
        for role, profile_attr, profile in (
            (UserType.FACULTY, "faculty_profile", FacultyProfile(
                id=15,
                employee_id="FAC-75",
                department=department,
                designation="Lecturer",
                address="Old faculty address",
            )),
            (UserType.STAFF, "staff_profile", StaffProfile(
                id=16,
                employee_id="STF-75",
                office=office,
                designation="Coordinator",
                address="Old staff address",
            )),
        ):
            with self.subTest(role=role):
                employee = User(
                    id=75,
                    username=f"{role}-75",
                    email=f"{role}-75@example.edu",
                    user_type=role,
                )
                profile.user = employee
                employee._state.fields_cache[profile_attr] = profile
                request = SimpleNamespace(user=employee)
                serializer = UserProfileSerializer(
                    instance=employee,
                    data={"address": "Updated employee address"},
                    partial=True,
                    context={"request": request},
                )
                self.assertTrue(serializer.is_valid(), serializer.errors)
                profile.save = Mock()
                serializer.save()
                self.assertEqual(profile.address, "Updated employee address")
                profile.save.assert_called_once_with(update_fields=["address", "updated_at"])

                protected = UserProfileSerializer(
                    instance=employee,
                    data={"employee_id": "CHANGED"},
                    partial=True,
                    context={"request": request},
                )
                self.assertFalse(protected.is_valid())
                self.assertIn("employee_id", protected.errors)

    def test_employee_profile_detail_write_permissions_remain_admin_only(self):
        for role, view in (
            (UserType.FACULTY, FacultyProfileDetailView),
            (UserType.STAFF, StaffProfileDetailView),
        ):
            with self.subTest(role=role):
                request = APIRequestFactory().patch("/api/accounts/profile/1/", {"address": "Attempt"})
                force_authenticate(
                    request,
                    user=User(id=76, username="employee", user_type=role),
                )
                response = view.as_view()(request, pk=1)
                self.assertEqual(response.status_code, 403)

    def test_admin_can_edit_employee_address_through_management_serializer(self):
        department = Department(id=17, name="Computing", code="CS")
        office = Office(id=18, name="Main Office", code="MO", department=department)
        for role, profile_attr, profile in (
            (UserType.FACULTY, "faculty_profile", FacultyProfile(
                id=19,
                employee_id="FAC-77",
                department=department,
                designation="Lecturer",
                address="Old address",
            )),
            (UserType.STAFF, "staff_profile", StaffProfile(
                id=20,
                employee_id="STF-77",
                office=office,
                designation="Coordinator",
                address="Old address",
            )),
        ):
            with self.subTest(role=role):
                employee = User(
                    id=77,
                    username=f"{role}-77",
                    email=f"{role}-77@example.edu",
                    user_type=role,
                )
                profile.user = employee
                employee._state.fields_cache[profile_attr] = profile
                serializer = AdminUserManagementSerializer(
                    instance=employee,
                    data={"address": "Admin-updated address"},
                    partial=True,
                )
                self.assertTrue(serializer.is_valid(), serializer.errors)
                profile.save = Mock()
                serializer.save()
                self.assertEqual(profile.address, "Admin-updated address")
                profile.save.assert_called_once()

    def test_faculty_and_staff_address_fields_are_nullable_model_fields(self):
        for profile_model in (FacultyProfile, StaffProfile):
            field = profile_model._meta.get_field("address")
            self.assertTrue(field.null)
            self.assertTrue(field.blank)

    def test_admin_self_can_edit_name_but_not_email_or_role(self):
        admin = User(
            id=78,
            username="admin78",
            email="admin78@example.edu",
            user_type=UserType.ADMIN,
            first_name="",
            last_name="",
        )
        context = {"request": SimpleNamespace(user=admin)}
        serializer = UserProfileSerializer(
            instance=admin,
            data={"first_name": "Admin", "last_name": ""},
            partial=True,
            context=context,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        admin.save = Mock()
        serializer.save()
        self.assertEqual(admin.first_name, "Admin")
        admin.save.assert_called_once()

        for field, value in (
            ("email", "changed@example.edu"),
            ("user_type", UserType.STUDENT),
        ):
            with self.subTest(field=field):
                denied = UserProfileSerializer(
                    instance=admin,
                    data={field: value},
                    partial=True,
                    context=context,
                )
                self.assertFalse(denied.is_valid())
                self.assertIn(field, denied.errors)

    def test_admin_management_endpoint_cannot_change_own_email_or_role(self):
        admin = User(id=79, username="admin79", email="admin79@example.edu", user_type=UserType.ADMIN)
        context = {"request": SimpleNamespace(user=admin)}
        for payload, field in (
            ({"email": "new-admin@example.edu"}, "email"),
            ({"user_type": UserType.STUDENT}, "user_type"),
        ):
            with self.subTest(field=field):
                serializer = AdminUserManagementSerializer(
                    instance=admin,
                    data=payload,
                    partial=True,
                    context=context,
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_admin_user_api_rejects_university_email_change(self):
        student = User(
            id=20,
            username="student-20",
            email="student20@example.edu",
            user_type=UserType.STUDENT,
        )
        filters = Mock()
        filters.exclude.return_value = filters
        filters.exists.return_value = False
        with patch("accounts.serializers.User.objects.filter", return_value=filters):
            serializer = UserSerializer(
                instance=student,
                data={"email": "new-address@example.edu"},
                partial=True,
            )
            self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_normal_user_api_cannot_promote_an_account_to_central_admin(self):
        student = User(
            id=23,
            username="student-23",
            email="student23@example.edu",
            user_type=UserType.STUDENT,
        )
        student.save = Mock()
        serializer = UserSerializer(
            instance=student,
            data={"user_type": UserType.ADMIN},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assertEqual(student.user_type, UserType.STUDENT)

    def test_non_student_profile_response_does_not_include_registration_number(self):
        faculty = User(
            id=18,
            username="faculty-18",
            email="faculty18@example.edu",
            user_type=UserType.FACULTY,
        )
        faculty._state.fields_cache["faculty_profile"] = None
        assignments = Mock()
        assignments.filter.return_value = assignments
        assignments.select_related.return_value = []
        with patch("accounts.serializers.ResponsibilityAssignment.objects.filter", return_value=assignments):
            result = UserProfileSerializer(faculty).data
        self.assertNotIn("registration_number", str(result))

    def test_student_profile_response_includes_registration_number(self):
        student = User(
            id=21,
            username="student-21",
            email="student21@example.edu",
            user_type=UserType.STUDENT,
        )
        profile = SimpleNamespace(
            registration_number="SP23-CS-0021",
            cgpa="3.50",
            date_of_birth=None,
            gender="",
            address="",
            emergency_contact="",
            guardian_name="",
            guardian_phone="",
            program=SimpleNamespace(name="Computer Science"),
            batch=SimpleNamespace(name="Sp23"),
            current_semester=SimpleNamespace(title="Semester 1"),
            academic_session=SimpleNamespace(title="Spring 2023"),
        )
        query = Mock()
        query.only.return_value = query
        query.filter.return_value = query
        query.first.return_value = profile
        with patch("accounts.serializers.StudentProfile.objects.select_related", return_value=query):
            result = UserProfileSerializer(student).data
        self.assertEqual(result["role_profile"]["registration_number"], "SP23-CS-0021")
        self.assertNotIn("guardian_name", result["role_profile"])
        self.assertNotIn("guardian_name", StudentProfileSerializer.Meta.fields)

    def test_employee_profile_response_includes_saved_address(self):
        department = Department(id=25, name="Computing", code="CS")
        office = Office(id=26, name="Main Office", code="MO", department=department)
        for role, profile_attr, profile in (
            (UserType.FACULTY, "faculty_profile", FacultyProfile(
                id=27,
                employee_id="FAC-27",
                department=department,
                designation="Lecturer",
                address="Faculty address",
            )),
            (UserType.STAFF, "staff_profile", StaffProfile(
                id=28,
                employee_id="STF-28",
                office=office,
                designation="Coordinator",
                address="Staff address",
            )),
        ):
            with self.subTest(role=role):
                employee = User(
                    id=profile.pk,
                    username=f"{role}-profile",
                    email=f"{role}-profile@example.edu",
                    user_type=role,
                )
                employee._state.fields_cache[profile_attr] = profile
                query = Mock()
                query.filter.return_value = query
                query.select_related.return_value = [ ]
                with patch("accounts.serializers.ResponsibilityAssignment.objects.filter", return_value=query):
                    result = UserProfileSerializer(employee).data
                self.assertEqual(result["role_profile"]["address"], profile.address)
                self.assertNotIn("registration_number", result["role_profile"])

    def test_profile_image_representation_uses_saved_image_url(self):
        admin = User(
            id=22,
            username="admin-22",
            email="admin22@example.edu",
            user_type=UserType.ADMIN,
        )
        admin.profile_picture = SimpleNamespace(
            name="profile_pictures/avatar.png",
            url="/media/profile_pictures/avatar.png",
        )
        request = APIRequestFactory().get("/api/accounts/me/profile/")
        result = UserProfileSerializer(admin, context={"request": request}).data
        self.assertEqual(
            result["profile_picture"],
            "http://testserver/media/profile_pictures/avatar.png",
        )

    def test_profile_picture_upload_is_validated_without_saving(self):
        image_buffer = BytesIO()
        Image.new("RGB", (1, 1), color=(20, 120, 100)).save(image_buffer, format="PNG")
        tiny_png = image_buffer.getvalue()
        student = User(
            id=19,
            username="student-19",
            email="student19@example.edu",
            user_type=UserType.STUDENT,
        )
        image = SimpleUploadedFile("profile.png", tiny_png, content_type="image/png")
        serializer = UserProfileSerializer(
            instance=student,
            data={"profile_picture": image},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["profile_picture"].name, "profile.png")

    def test_password_reset_token_round_trip_and_single_use(self):
        user = User(
            id=27,
            username="student-27",
            email="student27@example.edu",
            first_name="Student",
            last_name="Example",
            password=make_password("Previous-Password-2026!"),
            user_type=UserType.STUDENT,
        )
        encoded_uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        payload = {
            "uid": encoded_uid,
            "token": token,
            "new_password": "New-Unique-Password-2026!",
            "confirm_password": "New-Unique-Password-2026!",
        }

        with patch("accounts.serializers.User.objects.get", return_value=user):
            serializer = PasswordResetConfirmSerializer(data=payload)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            self.assertIs(serializer.validated_data["user"], user)

            user.set_password(payload["new_password"])
            reused = PasswordResetConfirmSerializer(data=payload)
            self.assertFalse(reused.is_valid())
            self.assertIn("detail", reused.errors)

    def test_email_link_generation_round_trips_through_confirmation_serializer(self):
        user = User(
            id=28,
            username="faculty-28",
            email="faculty28@example.edu",
            first_name="Faculty",
            last_name="Example",
            password=make_password("Previous-Password-2026!"),
            user_type=UserType.FACULTY,
        )
        with patch("accounts.views.send_mail") as mocked_send_mail:
            send_password_reset_email(user)

        mail_body = mocked_send_mail.call_args.kwargs["message"]
        reset_url = next(
            line for line in mail_body.splitlines()
            if "/reset-password/" in line
        )
        url_parts = reset_url.rstrip("/").split("/")
        encoded_uid, token = url_parts[-2:]
        payload = {
            "uid": encoded_uid,
            "token": token,
            "new_password": "A-Different-Strong-Password-2026!",
            "confirm_password": "A-Different-Strong-Password-2026!",
        }
        with patch("accounts.serializers.User.objects.get", return_value=user):
            serializer = PasswordResetConfirmSerializer(data=payload)
            self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_reset_confirmation_saves_a_hashed_password_without_database_access(self):
        user = User(
            id=29,
            username="staff-29",
            email="staff29@example.edu",
            first_name="Staff",
            last_name="Example",
            password=make_password("Previous-Password-2026!"),
            user_type=UserType.STAFF,
        )
        user.save = Mock()
        new_password = "Reset-Strong-Password-2026!"
        token = default_token_generator.make_token(user)
        request = APIRequestFactory().post(
            "/api/accounts/password-reset/confirm/",
            {
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": token,
                "new_password": new_password,
                "confirm_password": new_password,
            },
            format="json",
        )
        lookup = Mock()
        lookup.first.return_value = user
        with (
            patch("accounts.serializers.User.objects.get", return_value=user),
            patch("accounts.views.User.objects.select_for_update") as locked_query,
            patch("accounts.views.transaction.atomic", return_value=nullcontext()),
        ):
            locked_query.return_value.filter.return_value = lookup
            response = PasswordResetConfirmView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.check_password(new_password))
        self.assertNotEqual(user.password, new_password)
        user.save.assert_called_once()

    def test_student_reset_request_looks_up_registration_number(self):
        student = User(
            id=30,
            username="student-30",
            email="student30@example.edu",
            user_type=UserType.STUDENT,
        )
        profile = SimpleNamespace(user=student)
        query = Mock()
        query.filter.return_value.first.return_value = profile
        request = APIRequestFactory().post(
            "/api/accounts/password-reset/",
            {"identifier": "SP23-CS-0030"},
            format="json",
        )
        with (
            patch("accounts.views.StudentProfile.objects.select_related", return_value=query) as profile_lookup,
            patch("accounts.views.PasswordResetRequestThrottle.allow_request", return_value=True),
            patch("accounts.views.send_password_reset_email") as send_reset,
        ):
            response = PasswordResetRequestView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        profile_lookup.assert_called_once_with("user")
        query.filter.assert_called_once_with(registration_number="SP23-CS-0030")
        send_reset.assert_called_once_with(student)

    def test_staff_reset_request_uses_email_and_excludes_students(self):
        staff = User(
            id=33,
            username="staff-33",
            email="staff33@example.edu",
            user_type=UserType.STAFF,
        )
        query = Mock()
        query.exclude.return_value.first.return_value = staff
        request = APIRequestFactory().post(
            "/api/accounts/password-reset/",
            {"identifier": "staff33@example.edu"},
            format="json",
        )
        with (
            patch("accounts.views.User.objects.filter", return_value=query) as user_lookup,
            patch("accounts.views.PasswordResetRequestThrottle.allow_request", return_value=True),
            patch("accounts.views.send_password_reset_email") as send_reset,
        ):
            response = PasswordResetRequestView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        user_lookup.assert_called_once_with(email__iexact="staff33@example.edu")
        query.exclude.assert_called_once_with(user_type="student")
        send_reset.assert_called_once_with(staff)

    def test_password_reset_confirmation_must_match(self):
        serializer = PasswordResetConfirmSerializer(data={
            "uid": "unused",
            "token": "unused",
            "new_password": "New-Unique-Password-2026!",
            "confirm_password": "Different-Password-2026!",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("confirm_password", serializer.errors)

    def test_admin_password_endpoint_denies_every_non_admin_role(self):
        factory = APIRequestFactory()
        for role in (
            UserType.STUDENT,
            UserType.FACULTY,
            UserType.STAFF,
            UserType.EXTERNAL_EXAMINER,
        ):
            with self.subTest(role=role):
                user = User(id=31, username="account", user_type=role)
                request = factory.post(
                    "/api/accounts/users/32/set-password/",
                    {"new_password": "New-Unique-Password-2026!", "confirm_password": "New-Unique-Password-2026!"},
                    format="json",
                )
                force_authenticate(request, user=user)
                response = AdminSetPasswordView.as_view()(request, pk=32)
                self.assertEqual(response.status_code, 403)

    def test_admin_password_endpoint_hashes_password_without_database_access(self):
        target = User(
            id=32,
            username="target-32",
            email="target32@example.edu",
            user_type=UserType.STUDENT,
            password=make_password("Previous-Password-2026!"),
        )
        target.save = Mock()
        lookup = Mock()
        lookup.first.return_value = target
        admin = User(id=31, username="admin-31", user_type=UserType.ADMIN)
        request = APIRequestFactory().post(
            "/api/accounts/users/32/set-password/",
            {
                "new_password": "Admin-Set-Strong-Password-2026!",
                "confirm_password": "Admin-Set-Strong-Password-2026!",
            },
            format="json",
        )
        force_authenticate(request, user=admin)
        with patch("accounts.views.User.objects.filter", return_value=lookup):
            response = AdminSetPasswordView.as_view()(request, pk=32)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(target.check_password("Admin-Set-Strong-Password-2026!"))
        target.save.assert_called_once()

    def test_admin_permission_is_role_scoped(self):
        factory = RequestFactory()
        admin_request = factory.post("/unused/")
        admin_request.user = SimpleNamespace(is_authenticated=True, user_type=UserType.ADMIN)
        student_request = factory.post("/unused/")
        student_request.user = SimpleNamespace(is_authenticated=True, user_type=UserType.STUDENT)
        self.assertTrue(IsAdmin().has_permission(admin_request, None))
        self.assertFalse(IsAdmin().has_permission(student_request, None))

    def test_admin_password_serializer_rejects_email_and_registration_data(self):
        target = User(
            id=35,
            username="target-35",
            email="target35@example.edu",
            user_type=UserType.STUDENT,
        )
        serializer = AdminSetPasswordSerializer(
            data={
                "new_password": "New-Unique-Password-2026!",
                "confirm_password": "New-Unique-Password-2026!",
                "email": "changed@example.edu",
                "registration_number": "CHANGED-REG",
            },
            context={"target_user": target},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertIn("registration_number", serializer.errors)


class AuthenticationHardeningTests(SimpleTestCase):
    def test_inactive_email_user_cannot_login(self):
        inactive = User(
            id=36,
            username="inactive36",
            email="inactive36@example.edu",
            user_type=UserType.FACULTY,
            is_active=False,
        )
        inactive.check_password = Mock(return_value=True)
        with patch("accounts.serializers.User.objects.filter") as user_filter:
            user_filter.return_value.first.return_value = inactive
            serializer = EmailLoginSerializer(data={
                "email": "inactive36@example.edu",
                "password": "Test-Password-2026!",
            })
            self.assertFalse(serializer.is_valid())

    def test_reactivated_email_user_can_login(self):
        active = User(
            id=37,
            username="active37",
            email="active37@example.edu",
            user_type=UserType.STAFF,
            is_active=True,
        )
        active.check_password = Mock(return_value=True)
        with patch("accounts.serializers.User.objects.filter") as user_filter:
            user_filter.return_value.first.return_value = active
            serializer = EmailLoginSerializer(data={
                "email": "active37@example.edu",
                "password": "Test-Password-2026!",
            })
            self.assertTrue(serializer.is_valid(), serializer.errors)
            self.assertIs(serializer.validated_data["user"], active)

    def test_inactive_student_profile_cannot_login(self):
        inactive_user = User(
            id=38,
            username="inactive-student",
            email="inactive-student@example.edu",
            user_type=UserType.STUDENT,
            is_active=True,
        )
        inactive_user.check_password = Mock(return_value=True)
        profile = StudentProfile(
            id=38,
            registration_number="FA26-CS-038",
            user=inactive_user,
            is_active=False,
        )
        profile.user = inactive_user
        with patch("accounts.serializers.StudentProfile.objects.select_related") as select_related:
            select_related.return_value.get.return_value = profile
            serializer = StudentLoginSerializer(data={
                "registration_number": "FA26-CS-038",
                "password": "Test-Password-2026!",
            })
            self.assertFalse(serializer.is_valid())

    def test_generic_user_serializer_cannot_create_or_change_roles(self):
        filters = Mock()
        filters.exclude.return_value = filters
        filters.exists.return_value = False
        with patch("accounts.serializers.User.objects.filter", return_value=filters):
            serializer = UserSerializer(
                data={
                    "username": "bypass",
                    "password": "Bypass-Password-2026!",
                    "email": "bypass@example.edu",
                    "user_type": "admin",
                },
            )
            self.assertTrue(serializer.is_valid(), serializer.errors)
            with self.assertRaises(serializers.ValidationError):
                serializer.save()

        student = User(
            id=39,
            username="student39",
            email="student39@example.edu",
            user_type=UserType.STUDENT,
        )
        student.save = Mock()
        serializer = UserSerializer(
            instance=student,
            data={"user_type": UserType.ADMIN},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assertEqual(student.user_type, UserType.STUDENT)

    def test_change_password_clears_forced_password_flag(self):
        user = User(
            id=40,
            username="forced40",
            email="forced40@example.edu",
            user_type=UserType.STAFF,
            password=make_password("Initial-Password-2026!"),
            must_change_password=True,
        )
        user.save = Mock()
        request = APIRequestFactory().post(
            "/api/accounts/change-password/",
            {
                "current_password": "Initial-Password-2026!",
                "new_password": "Changed-Password-2026!",
            },
            format="json",
        )
        force_authenticate(request, user=user)

        response = ChangePasswordView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(user.must_change_password)
        self.assertTrue(user.check_password("Changed-Password-2026!"))
        user.save.assert_called_once()

    def test_login_throttle_is_identifier_and_ip_scoped(self):
        from accounts.views import LoginRateThrottle

        throttle = LoginRateThrottle()
        django_request = APIRequestFactory().post(
            "/api/accounts/email-login/",
            {"email": "Staff@Example.edu", "password": "wrong"},
        )
        django_request.META["REMOTE_ADDR"] = "127.0.0.1"
        cache_key = throttle.get_cache_key(django_request, SimpleNamespace())
        self.assertIn("staff@example.edu", cache_key)
        self.assertIn("127.0.0.1", cache_key)

