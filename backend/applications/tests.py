import tempfile
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import (
    AcademicSession,
    Batch,
    Department,
    FacultyProfile,
    Office,
    Program,
    ResponsibilityAssignment,
    Semester,
    StaffProfile,
    StudentProfile,
    User,
)
from applications.models import (
    Application,
    ApplicationField,
    ApplicationFieldOption,
    ApplicationPriority,
    ApplicationStatus,
    ApplicationType,
    ActionType,
    ApprovalLog,
    Attachment,
    Comment,
    Workflow,
    WorkflowStep,
)
from applications.views import AdminAnalyticsView


class UnifiedApplicationManagementTests(APITestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()

        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
        )
        self.other_department = Department.objects.create(
            name="Management Sciences",
            code="MS",
        )
        self.program = Program.objects.create(
            name="BS Computer Science",
            code="BSCS",
            department=self.department,
            duration_years=4,
        )
        self.other_program = Program.objects.create(
            name="BS Management Sciences",
            code="BSMS",
            department=self.other_department,
            duration_years=4,
        )
        self.session = AcademicSession.objects.create(
            title="Fall 2026",
            session_type="fall",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 1, 31),
            is_current=True,
        )
        self.semester = Semester.objects.create(number=1, title="Semester 1")
        self.batch = Batch.objects.create(
            name="Fa26",
            program=self.program,
            admission_year=2026,
            graduation_year=2030,
        )
        self.other_batch = Batch.objects.create(
            name="Fa26-MS",
            program=self.other_program,
            admission_year=2026,
            graduation_year=2030,
        )

        self.student_user = self.create_user("student", "student")
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            registration_number="FA26-BSCS-001",
            program=self.program,
            batch=self.batch,
            current_semester=self.semester,
            academic_session=self.session,
        )
        self.other_student_user = self.create_user("student2", "student")
        self.other_student = StudentProfile.objects.create(
            user=self.other_student_user,
            registration_number="FA26-BSMS-001",
            program=self.other_program,
            batch=self.other_batch,
            current_semester=self.semester,
            academic_session=self.session,
        )

        self.advisor_user = self.create_user("advisor", "faculty")
        self.advisor = FacultyProfile.objects.create(
            user=self.advisor_user,
            employee_id="FAC-ADV-001",
            department=self.department,
            designation="Lecturer",
        )
        self.hod_user = self.create_user("hod", "faculty")
        self.hod = FacultyProfile.objects.create(
            user=self.hod_user,
            employee_id="FAC-HOD-001",
            department=self.department,
            designation="Associate Professor",
        )
        self.other_hod_user = self.create_user("other-hod", "faculty")
        self.other_hod = FacultyProfile.objects.create(
            user=self.other_hod_user,
            employee_id="FAC-HOD-002",
            department=self.other_department,
            designation="Professor",
        )
        self.admin_user = self.create_user("admin", "admin")

        self.office = Office.objects.create(
            name="Academic Office",
            code="ACADEMIC",
            department=self.department,
            is_active=True,
        )

        ResponsibilityAssignment.objects.create(
            faculty=self.advisor,
            department=self.department,
            office=self.office,
            batch=self.batch,
            responsibility_type="advisor",
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        ResponsibilityAssignment.objects.create(
            faculty=self.hod,
            department=self.department,
            office=self.office,
            batch=None,
            responsibility_type="hod",
            start_date=date(2026, 1, 1),
            is_active=True,
        )
        ResponsibilityAssignment.objects.create(
            faculty=self.other_hod,
            department=self.other_department,
            office=self.office,
            batch=None,
            responsibility_type="hod",
            start_date=date(2026, 1, 1),
            is_active=True,
        )

        self.application_type = ApplicationType.objects.create(
            name="Course Registration",
            description="Register for a course",
            office=self.office,
            is_active=True,
        )
        self.course_code_field = ApplicationField.objects.create(
            application_type=self.application_type,
            label="Course Code",
            field_name="course_code",
            field_type="text",
            is_required=True,
            display_order=1,
        )
        self.semester_field = ApplicationField.objects.create(
            application_type=self.application_type,
            label="Semester",
            field_name="semester",
            field_type="dropdown",
            is_required=True,
            display_order=2,
        )
        ApplicationFieldOption.objects.create(
            field=self.semester_field,
            label="Fall",
            value="Fall",
        )
        ApplicationFieldOption.objects.create(
            field=self.semester_field,
            label="Spring",
            value="Spring",
        )

        self.workflow = Workflow.objects.create(
            application_type=self.application_type,
            workflow_name="Course Registration Workflow",
            is_active=True,
        )
        self.advisor_step = WorkflowStep.objects.create(
            workflow=self.workflow,
            office=self.office,
            step_name="Advisor Review",
            step_order=1,
            required_responsibility="advisor",
            can_approve=True,
            can_reject=True,
            can_request_revision=True,
        )
        self.hod_step = WorkflowStep.objects.create(
            workflow=self.workflow,
            office=self.office,
            step_name="HOD Review",
            step_order=2,
            required_responsibility="hod",
            can_approve=True,
            can_reject=True,
            can_request_revision=True,
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_directory.cleanup()
        super().tearDown()

    def create_user(self, username, user_type):
        return User.objects.create_user(
            username=username,
            email=f"{username}@intellicampus.test",
            password="Test-Password-2026!",
            user_type=user_type,
        )

    def submit_application(self, application_type=None, form_data=None):
        application_type = application_type or self.application_type
        if form_data is None:
            form_data = {"course_code": "CS101", "semester": "Fall"}
        self.client.force_authenticate(self.student_user)
        return self.client.post(
            reverse("application-list-create"),
            {
                "application_type": application_type.id,
                "title": application_type.name,
                "description": "Test application",
                "form_data": form_data,
            },
            format="json",
        )

    def create_simple_application(self, status=ApplicationStatus.SUBMITTED):
        application = Application.objects.create(
            application_type=self.application_type,
            student=self.student,
            workflow=self.workflow,
            current_step=self.advisor_step,
            title="Course Registration",
            description="Test application",
            form_data={"course_code": "CS101", "semester": "Fall"},
            status=status,
            submitted_at=timezone.now() if status != ApplicationStatus.DRAFT else None,
        )
        return application

    def test_valid_dynamic_submission(self):
        response = self.submit_application()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        application = Application.objects.get(pk=response.data["id"])
        self.assertEqual(application.status, ApplicationStatus.SUBMITTED)
        self.assertEqual(application.current_step, self.advisor_step)
        self.assertEqual(application.priority, ApplicationPriority.LOW)
        self.assertIsNotNone(application.submitted_at)

    def test_missing_required_dynamic_field_is_rejected(self):
        response = self.submit_application(
            form_data={"course_code": "CS101"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("semester", response.data)

    def test_unknown_and_mismatched_dynamic_fields_are_rejected(self):
        response = self.submit_application(
            form_data={
                "course_code": "CS101",
                "semester": "Fall",
                "scholarship_name": "Wrong field",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("form_data", response.data)

    def test_invalid_dropdown_option_is_rejected(self):
        response = self.submit_application(
            form_data={"course_code": "CS101", "semester": "Summer"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("semester", response.data)

    def test_predefined_application_type_priority_rules(self):
        cases = [
            ("Degree Application", ApplicationPriority.HIGH),
            ("Fee Installment", ApplicationPriority.HIGH),
            ("Transcript", ApplicationPriority.MEDIUM),
            ("Course Registration", ApplicationPriority.LOW),
            ("Unlisted Request", ApplicationPriority.MEDIUM),
        ]

        for name, expected in cases:
            with self.subTest(name=name):
                application_type, _ = ApplicationType.objects.get_or_create(
                    name=name,
                    defaults={
                        "office": self.office,
                        "is_active": True,
                    },
                )
                if name == "Course Registration":
                    application_type = self.application_type
                workflow = Workflow.objects.create(
                    application_type=application_type,
                    workflow_name=f"{name} Workflow",
                    is_active=True,
                )
                step = WorkflowStep.objects.create(
                    workflow=workflow,
                    office=self.office,
                    step_name="Review",
                    step_order=1,
                    can_approve=True,
                )
                application = Application.objects.create(
                    application_type=application_type,
                    student=self.student,
                    workflow=workflow,
                    current_step=step,
                    title=name,
                    description="Priority test",
                    form_data={},
                    status=ApplicationStatus.SUBMITTED,
                )
                self.assertEqual(application.priority, expected)

    def test_advisor_and_hod_routing_and_authorization(self):
        application = self.create_simple_application()

        self.client.force_authenticate(self.create_user("wrong-advisor", "faculty"))
        wrong_advisor = FacultyProfile.objects.create(
            user=User.objects.get(username="wrong-advisor"),
            employee_id="FAC-WRONG",
            department=self.department,
            designation="Lecturer",
        )
        wrong_response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.APPROVED, "remarks": ""},
            format="json",
        )
        self.assertEqual(wrong_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.advisor_user)
        forward_response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.APPROVED, "remarks": "Approved by advisor"},
            format="json",
        )
        self.assertEqual(forward_response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.IN_PROGRESS)
        self.assertEqual(application.current_step, self.hod_step)

        self.client.force_authenticate(self.other_hod_user)
        wrong_hod_response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.APPROVED, "remarks": ""},
            format="json",
        )
        self.assertEqual(wrong_hod_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.hod_user)
        final_response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.APPROVED, "remarks": "Approved by HOD"},
            format="json",
        )
        self.assertEqual(final_response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.APPROVED)

    def test_rejection_requires_remarks_and_finalizes_application(self):
        application = self.create_simple_application()
        self.client.force_authenticate(self.advisor_user)

        missing_remarks = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.REJECTED, "remarks": ""},
            format="json",
        )
        self.assertEqual(missing_remarks.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.REJECTED, "remarks": "Incomplete records"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.REJECTED)
        self.assertIsNotNone(application.completed_at)

    def test_revision_resubmission_and_tracking_history(self):
        application = self.create_simple_application()
        self.client.force_authenticate(self.advisor_user)
        revision = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.REVISION_REQUIRED, "remarks": "Correct the course code"},
            format="json",
        )
        self.assertEqual(revision.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.REVISION_REQUIRED)

        inbox = self.client.get(reverse("officer-inbox"))
        self.assertEqual(inbox.status_code, status.HTTP_200_OK)
        self.assertNotIn(application.id, [item["id"] for item in inbox.data])

        self.client.force_authenticate(self.student_user)
        resubmit = self.client.post(
            reverse("application-resubmit", args=[application.id]),
            {
                "title": "Corrected Course Registration",
                "form_data": {"course_code": "CS102", "semester": "Spring"},
            },
            format="json",
        )
        self.assertEqual(resubmit.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.IN_PROGRESS)
        self.assertEqual(application.form_data["course_code"], "CS102")
        self.assertTrue(application.approval_logs.filter(action=ActionType.RESUBMITTED).exists())

        self.client.force_authenticate(self.advisor_user)
        inbox = self.client.get(reverse("officer-inbox"))
        self.assertEqual(inbox.status_code, status.HTTP_200_OK)
        self.assertIn(application.id, [item["id"] for item in inbox.data])

    def test_comment_and_approval_history_are_recorded(self):
        application = self.create_simple_application()
        self.client.force_authenticate(self.student_user)
        comment_response = self.client.post(
            reverse("comment-list-create"),
            {"application": application.id, "comment": "Please review this request"},
            format="json",
        )
        self.assertEqual(comment_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comment.objects.filter(application=application).exists())

        ApprovalLog.objects.create(
            application=application,
            workflow_step=self.advisor_step,
            action_by=self.advisor_user,
            action=ActionType.APPROVED,
            remarks="Checked",
        )
        history_response = self.client.get(
            reverse("approval-log-list-create"),
            {"application": application.id},
        )
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)

    def test_attachment_upload_access_and_finalized_validation(self):
        application = self.create_simple_application()
        self.client.force_authenticate(self.student_user)
        upload = self.client.post(
            reverse("attachment-list-create"),
            {
                "application": application.id,
                "file_name": "support.pdf",
                "file_path": SimpleUploadedFile(
                    "support.pdf",
                    b"%PDF-test",
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        self.assertEqual(upload.status_code, status.HTTP_201_CREATED)
        attachment = Attachment.objects.get(pk=upload.data["id"])
        self.assertEqual(attachment.uploaded_by, self.student_user)

        other_application = Application.objects.create(
            application_type=self.application_type,
            student=self.other_student,
            workflow=self.workflow,
            current_step=self.advisor_step,
            title="Other Student Application",
            description="Different student",
            form_data={"course_code": "CS201", "semester": "Fall"},
            status=ApplicationStatus.SUBMITTED,
        )
        wrong_upload = self.client.post(
            reverse("attachment-list-create"),
            {
                "application": other_application.id,
                "file_name": "wrong.pdf",
                "file_path": SimpleUploadedFile(
                    "wrong.pdf",
                    b"%PDF-test",
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        self.assertEqual(wrong_upload.status_code, status.HTTP_403_FORBIDDEN)

        application.status = ApplicationStatus.APPROVED
        application.completed_at = timezone.now()
        application.save(update_fields=["status", "completed_at"])

        finalized_upload = self.client.post(
            reverse("attachment-list-create"),
            {
                "application": application.id,
                "file_name": "late.pdf",
                "file_path": SimpleUploadedFile(
                    "late.pdf",
                    b"%PDF-test",
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        self.assertEqual(finalized_upload.status_code, status.HTTP_403_FORBIDDEN)

        delete_response = self.client.delete(
            reverse("attachment-detail", args=[attachment.id]),
        )
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Attachment.objects.filter(pk=attachment.id).exists())

    def test_finalized_application_rejects_comments_and_workflow_actions(self):
        application = self.create_simple_application(ApplicationStatus.APPROVED)
        application.completed_at = timezone.now()
        application.save(update_fields=["completed_at"])

        self.client.force_authenticate(self.student_user)
        comment_response = self.client.post(
            reverse("comment-list-create"),
            {"application": application.id, "comment": "Late comment"},
            format="json",
        )
        self.assertEqual(comment_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.advisor_user)
        action_response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.APPROVED, "remarks": "Double action"},
            format="json",
        )
        self.assertEqual(action_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_responsible_officer_information(self):
        application = self.create_simple_application()
        self.client.force_authenticate(self.student_user)

        response = self.client.get(
            reverse("application-tracking", args=[application.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        officer = response.data["current_officer"]
        self.assertEqual(officer["id"], self.advisor_user.id)
        self.assertEqual(officer["responsibility_code"], "advisor")
        self.assertEqual(officer["office"], self.office.name)

    def test_admin_override_can_finalize_application(self):
        application = self.create_simple_application()
        self.client.force_authenticate(self.admin_user)

        forward_response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.APPROVED, "remarks": "Administrative override"},
            format="json",
        )
        self.assertEqual(forward_response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.IN_PROGRESS)
        self.assertEqual(application.current_step, self.hod_step)

        final_response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.APPROVED, "remarks": "Administrative final approval"},
            format="json",
        )
        self.assertEqual(final_response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.APPROVED)

    def test_advisor_scope_rejects_other_batch(self):
        application = Application.objects.create(
            application_type=self.application_type,
            student=self.other_student,
            workflow=self.workflow,
            current_step=self.advisor_step,
            title="Other Batch Application",
            description="Other batch",
            form_data={"course_code": "MS101", "semester": "Fall"},
            status=ApplicationStatus.SUBMITTED,
        )

        self.client.force_authenticate(self.advisor_user)
        response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.APPROVED, "remarks": ""},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hod_scope_rejects_other_department(self):
        application = Application.objects.create(
            application_type=self.application_type,
            student=self.other_student,
            workflow=self.workflow,
            current_step=self.hod_step,
            title="Other Department Application",
            description="Other department",
            form_data={"course_code": "MS101", "semester": "Fall"},
            status=ApplicationStatus.IN_PROGRESS,
        )

        self.client.force_authenticate(self.hod_user)
        response = self.client.post(
            reverse("application-action", args=[application.id]),
            {"action": ActionType.APPROVED, "remarks": ""},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminAnalyticsTests(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Analytics Department",
            code="ANL",
        )
        self.program = Program.objects.create(
            name="BS Analytics",
            code="BSAN",
            department=self.department,
            duration_years=4,
        )
        self.session = AcademicSession.objects.create(
            title="Fall 2026 Analytics",
            session_type="fall",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 1, 31),
            is_current=True,
        )
        self.semester = Semester.objects.create(
            number=1,
            title="Semester 1",
        )
        self.batch = Batch.objects.create(
            name="Fa26-ANL",
            program=self.program,
            admission_year=2026,
            graduation_year=2030,
        )

        self.admin_user = User.objects.create_user(
            username="analytics-admin",
            email="analytics-admin@intellicampus.test",
            password="Test-Password-2026!",
            user_type="admin",
        )
        self.student_user = User.objects.create_user(
            username="analytics-student",
            email="analytics-student@intellicampus.test",
            password="Test-Password-2026!",
            user_type="student",
        )
        self.faculty_user = User.objects.create_user(
            username="analytics-faculty",
            email="analytics-faculty@intellicampus.test",
            password="Test-Password-2026!",
            user_type="faculty",
        )
        self.staff_user = User.objects.create_user(
            username="analytics-staff",
            email="analytics-staff@intellicampus.test",
            password="Test-Password-2026!",
            user_type="staff",
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            registration_number="FA26-BSAN-001",
            program=self.program,
            batch=self.batch,
            current_semester=self.semester,
            academic_session=self.session,
        )

        self.office = Office.objects.create(
            name="Analytics Office",
            code="ANL-OFFICE",
            department=self.department,
        )
        self.application_type = ApplicationType.objects.create(
            name="Analytics Request",
            office=self.office,
        )
        self.workflow = Workflow.objects.create(
            application_type=self.application_type,
            workflow_name="Analytics Workflow",
            is_active=True,
        )
        self.step = WorkflowStep.objects.create(
            workflow=self.workflow,
            office=self.office,
            step_name="Review",
            step_order=1,
            can_approve=True,
        )

    def test_admin_analytics_returns_real_aggregates(self):
        Application.objects.create(
            application_type=self.application_type,
            student=self.student,
            workflow=self.workflow,
            current_step=self.step,
            title="Analytics Application",
            description="Test",
            form_data={},
            status=ApplicationStatus.APPROVED,
            submitted_at=timezone.now(),
            completed_at=timezone.now(),
        )

        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("admin-analytics"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["totals"]["students"], 1)
        self.assertEqual(response.data["totals"]["faculty"], 1)
        self.assertEqual(response.data["totals"]["staff"], 1)
        self.assertEqual(response.data["totals"]["applications"], 1)
        self.assertEqual(response.data["application_status"]["approved"], 1)
        self.assertEqual(
            response.data["department_distribution"],
            [{"department": "Analytics Department", "count": 1}],
        )
        self.assertEqual(
            response.data["semester_distribution"],
            [{"semester": "Semester 1", "number": 1, "count": 1}],
        )
        self.assertEqual(
            response.data["application_types"],
            [{"application_type": "Analytics Request", "count": 1}],
        )
        self.assertEqual(len(response.data["monthly_submissions"]), 1)
        self.assertEqual(len(response.data["monthly_completions"]), 1)
        self.assertFalse(response.data["forecast"]["available"])

    def test_analytics_empty_dataset_is_safe(self):
        self.student_user.is_active = False
        self.student_user.save(update_fields=["is_active"])
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("admin-analytics"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["totals"]["applications"], 0)
        self.assertEqual(response.data["department_distribution"], [])
        self.assertEqual(response.data["semester_distribution"], [])
        self.assertEqual(response.data["application_types"], [])
        self.assertEqual(response.data["monthly_submissions"], [])
        self.assertEqual(response.data["monthly_completions"], [])
        self.assertFalse(response.data["forecast"]["available"])

    def test_analytics_requires_admin_role(self):
        for user in (self.student_user, self.faculty_user, self.staff_user):
            with self.subTest(user=user.username):
                self.client.force_authenticate(user)
                response = self.client.get(reverse("admin-analytics"))
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_forecast_fills_missing_calendar_months_and_predicts_next_months(self):
        forecast = AdminAnalyticsView.build_submission_forecast([
            {"month": "2024-01", "count": 2},
            {"month": "2024-03", "count": 4},
            {"month": "2024-07", "count": 3},
        ])

        self.assertTrue(forecast["available"])
        self.assertEqual(
            forecast["actual"],
            [
                {"month": "2024-01", "count": 2},
                {"month": "2024-02", "count": 0},
                {"month": "2024-03", "count": 4},
                {"month": "2024-04", "count": 0},
                {"month": "2024-05", "count": 0},
                {"month": "2024-06", "count": 0},
                {"month": "2024-07", "count": 3},
            ],
        )
        self.assertEqual(
            [item["month"] for item in forecast["predicted"]],
            ["2024-08", "2024-09", "2024-10"],
        )

    def test_forecast_requires_six_months_and_three_active_months(self):
        sparse_activity = AdminAnalyticsView.build_submission_forecast([
            {"month": "2023-01", "count": 1},
            {"month": "2023-12", "count": 2},
        ])
        short_history = AdminAnalyticsView.build_submission_forecast([
            {"month": "2024-01", "count": 1},
            {"month": "2024-03", "count": 2},
            {"month": "2024-05", "count": 3},
        ])

        self.assertFalse(sparse_activity["available"])
        self.assertFalse(short_history["available"])
        self.assertEqual(sparse_activity["predicted"], [])
        self.assertEqual(short_history["predicted"], [])
