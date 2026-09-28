
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ResponsibilityAssignment
from accounts.permissions import IsAdminOrReadOnly

from .models import (
    ApplicationType,
    ApplicationField,
    ApplicationFieldOption,
    Workflow,
    WorkflowStep,
    ApplicationStatus,
    ActionType,
    Application,
    Attachment,
    Comment,
    ApprovalLog,
)

from .serializers import (
    ApplicationTypeSerializer,
    ApplicationFieldSerializer,
    ApplicationFieldOptionSerializer,
    WorkflowSerializer,
    WorkflowStepSerializer,
    ApplicationSerializer,
    AttachmentSerializer,
    ApplicationResubmitSerializer,
    CommentSerializer,
    ApprovalLogSerializer,
)


# =========================================================
# ADMIN-MANAGED APPLICATION CONFIGURATION
# =========================================================

class ApplicationTypeListCreateView(generics.ListCreateAPIView):
    queryset = ApplicationType.objects.all()
    serializer_class = ApplicationTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class ApplicationTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ApplicationType.objects.all()
    serializer_class = ApplicationTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class ApplicationFieldListCreateView(generics.ListCreateAPIView):
    queryset = ApplicationField.objects.all()
    serializer_class = ApplicationFieldSerializer
    permission_classes = [IsAdminOrReadOnly]


class ApplicationFieldDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ApplicationField.objects.all()
    serializer_class = ApplicationFieldSerializer
    permission_classes = [IsAdminOrReadOnly]


class ApplicationFieldOptionListCreateView(generics.ListCreateAPIView):
    queryset = ApplicationFieldOption.objects.all()
    serializer_class = ApplicationFieldOptionSerializer
    permission_classes = [IsAdminOrReadOnly]


class ApplicationFieldOptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ApplicationFieldOption.objects.all()
    serializer_class = ApplicationFieldOptionSerializer
    permission_classes = [IsAdminOrReadOnly]


class WorkflowListCreateView(generics.ListCreateAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [IsAdminOrReadOnly]


class WorkflowDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [IsAdminOrReadOnly]


class WorkflowStepListCreateView(generics.ListCreateAPIView):
    queryset = WorkflowStep.objects.all()
    serializer_class = WorkflowStepSerializer
    permission_classes = [IsAdminOrReadOnly]


class WorkflowStepDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WorkflowStep.objects.all()
    serializer_class = WorkflowStepSerializer
    permission_classes = [IsAdminOrReadOnly]


# =========================================================
# OFFICER APPLICATION ACCESS
# OFFICE + RESPONSIBILITY + DEPARTMENT + BATCH
# =========================================================

def get_officer_applications(user):

    # Only faculty and staff can access officer inbox
    if user.user_type not in ("faculty", "staff"):
        return Application.objects.none()

    today = timezone.localdate()

    # Find active responsibility assignments
    assignments = (
        ResponsibilityAssignment.objects
        .filter(
            is_active=True,
            start_date__lte=today,
            office__isnull=False,
        )
        .filter(
            Q(end_date__isnull=True) |
            Q(end_date__gte=today)
        )
        .filter(
            Q(faculty__user=user) |
            Q(staff__user=user)
        )
    )

    # Initially no applications are accessible
    application_filter = Q(pk__in=[])

    for assignment in assignments:

        # Advisor must have an assigned batch
        if (
            assignment.responsibility_type == "advisor"
            and not assignment.batch_id
        ):
            continue

        # HOD must have an assigned department
        if (
            assignment.responsibility_type == "hod"
            and not assignment.department_id
        ):
            continue

        # Match current office AND responsibility
        condition = Q(
            current_step__office_id=assignment.office_id,
            current_step__required_responsibility=(
                assignment.responsibility_type
            ),
        )

        # Match department if assignment is
        # department-specific
        if assignment.department_id:

            condition &= Q(
                student__program__department_id=(
                    assignment.department_id
                )
            )

        # Match batch if assignment is batch-specific
        if assignment.batch_id:

            condition &= Q(
                student__batch_id=assignment.batch_id
            )

        application_filter |= condition

    # Return applications waiting for officer action
    return (
        Application.objects
        .filter(
            application_filter,
            status__in=[
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.IN_PROGRESS,
            ],
        )
        .select_related(
            "student",
            "student__user",
            "application_type",
            "current_step",
            "workflow",
        )
        .distinct()
    )


# =========================================================
# APPLICATIONS
# =========================================================

class ApplicationListCreateView(
    generics.ListCreateAPIView
):

    queryset = Application.objects.all()

    serializer_class = ApplicationSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        # Admin can see all applications
        if user.user_type == "admin":

            return Application.objects.all()

        # Student can see own applications
        if user.user_type == "student":

            return Application.objects.filter(
                student__user=user
            )

        # Faculty/staff use dedicated officer inbox
        return Application.objects.none()

    def perform_create(self, serializer):

        if self.request.user.user_type != "student":

            raise PermissionDenied(
                "Only students can submit applications."
            )

        serializer.save()


# =========================================================
# APPLICATION DETAIL
# =========================================================

class ApplicationDetailView(
    generics.RetrieveAPIView
):

    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        # Admin can view every application
        if user.user_type == "admin":
            return Application.objects.all()

        # Student can view only own applications
        if user.user_type == "student":
            return Application.objects.filter(
                student__user=user
            )

        # Faculty / staff can view applications
        # currently assigned to them
        if user.user_type in ["faculty", "staff"]:
            return get_officer_applications(user)

        return Application.objects.none()


# =========================================================
# GENERAL APPLICATION ACCESS
# =========================================================

def get_accessible_applications(user):

    # Admin can access every application
    if user.user_type == "admin":
        return Application.objects.all()

    # Student can access only own applications
    if user.user_type == "student":
        return Application.objects.filter(
            student__user=user
        )

    # Faculty / staff can access applications
    # currently assigned to them
    if user.user_type in ["faculty", "staff"]:
        return get_officer_applications(user)

    return Application.objects.none()

# =========================================================
# ATTACHMENTS
# =========================================================

class AttachmentListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        accessible_applications = (
            get_accessible_applications(
                self.request.user
            )
        )

        queryset = (
            Attachment.objects
            .filter(
                application__in=accessible_applications
            )
            .select_related(
                "application",
                "uploaded_by",
            )
        )

        # Optional:
        # /attachments/?application=4
        application_id = (
            self.request.query_params.get(
                "application"
            )
        )

        if application_id:
            queryset = queryset.filter(
                application_id=application_id
            )

        return queryset

    def perform_create(self, serializer):

        application_id = (
            self.request.data.get("application")
        )

        if not application_id:

            raise PermissionDenied(
                "Application is required."
            )

        accessible_application = (
            get_accessible_applications(
                self.request.user
            )
            .filter(pk=application_id)
            .first()
        )

        if not accessible_application:

            raise PermissionDenied(
                "You do not have access to this application."
            )

        # Finalized applications should not be modified
        if accessible_application.status in [
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.CANCELLED,
        ]:

            raise PermissionDenied(
                "Attachments cannot be added "
                "to a finalized application."
            )

        serializer.save(
            uploaded_by=self.request.user
        )

class AttachmentDetailView(
    generics.RetrieveDestroyAPIView
):

    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        accessible_applications = (
            get_accessible_applications(
                self.request.user
            )
        )

        return Attachment.objects.filter(
            application__in=accessible_applications
        )

    def perform_destroy(self, instance):

        user = self.request.user

        # Admin can delete
        if user.user_type == "admin":
            instance.delete()
            return

        # Only original uploader can delete
        if instance.uploaded_by_id != user.id:

            raise PermissionDenied(
                "You cannot delete another user's attachment."
            )

        # Do not change finalized application records
        if instance.application.status in [
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.CANCELLED,
        ]:

            raise PermissionDenied(
                "Attachments of a finalized application "
                "cannot be deleted."
            )

        instance.delete()

# =========================================================
# COMMENTS
# =========================================================

class CommentListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        accessible_applications = (
            get_accessible_applications(
                self.request.user
            )
        )

        queryset = (
            Comment.objects
            .filter(
                application__in=accessible_applications
            )
            .select_related(
                "application",
                "user",
            )
        )

        application_id = (
            self.request.query_params.get(
                "application"
            )
        )

        if application_id:

            queryset = queryset.filter(
                application_id=application_id
            )

        return queryset

    def perform_create(self, serializer):

        application_id = (
            self.request.data.get("application")
        )

        if not application_id:

            raise PermissionDenied(
                "Application is required."
            )

        accessible_application = (
            get_accessible_applications(
                self.request.user
            )
            .filter(pk=application_id)
            .first()
        )

        if not accessible_application:

            raise PermissionDenied(
                "You do not have access to this application."
            )

        serializer.save(
            user=self.request.user
        )

class CommentDetailView(
    generics.RetrieveAPIView
):

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        accessible_applications = (
            get_accessible_applications(
                self.request.user
            )
        )

        return Comment.objects.filter(
            application__in=accessible_applications
        )

# =========================================================
# APPROVAL LOGS
# =========================================================

class ApprovalLogListCreateView(generics.ListAPIView):

    serializer_class = ApprovalLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        accessible_applications = (
            get_accessible_applications(
                self.request.user
            )
        )

        queryset = (
            ApprovalLog.objects
            .filter(
                application__in=accessible_applications
            )
            .select_related(
                "application",
                "workflow_step",
                "action_by",
            )
            .order_by("action_date")
        )

        # Optional filter:
        # /approval-logs/?application=4
        application_id = (
            self.request.query_params.get(
                "application"
            )
        )

        if application_id:
            queryset = queryset.filter(
                application_id=application_id
            )

        return queryset


class ApprovalLogDetailView(generics.RetrieveAPIView):

    serializer_class = ApprovalLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        accessible_applications = (
            get_accessible_applications(
                self.request.user
            )
        )

        return ApprovalLog.objects.filter(
            application__in=accessible_applications
        )

# =========================================================
# OFFICER INBOX VIEW
# =========================================================

class OfficerInboxView(
    generics.ListAPIView
):

    serializer_class = ApplicationSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        # Admin can see all pending applications
        if user.user_type == "admin":

            return Application.objects.filter(
                status__in=[
                    ApplicationStatus.SUBMITTED,
                    ApplicationStatus.IN_PROGRESS,
                ]
            )

        # Faculty/staff get scoped applications
        return get_officer_applications(user)


# =========================================================
# APPLICATION ACTION VIEW
# APPROVE / REJECT / REVISION REQUIRED
# =========================================================

class ApplicationActionView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        # ------------------------------------------------
        # 1. Get action and remarks
        # ------------------------------------------------

        action = request.data.get("action")

        remarks = request.data.get("remarks", "")

        valid_actions = [
            ActionType.APPROVED,
            ActionType.REJECTED,
            ActionType.REVISION_REQUIRED,
        ]

        # ------------------------------------------------
        # 2. Validate action
        # ------------------------------------------------

        if action not in valid_actions:

            return Response(
                {
                    "detail": (
                        "Invalid action. Use approved, "
                        "rejected, or revision_required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------------------------------------
        # 3. Start database transaction
        # ------------------------------------------------

        with transaction.atomic():

            try:

                application = (
                    Application.objects
                    .select_for_update()
                    .select_related("workflow")
                    .get(pk=pk)
                )

            except Application.DoesNotExist:

                return Response(
                    {
                        "detail": "Application not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ------------------------------------------------
            # 4. Finalized applications cannot change
            # ------------------------------------------------

            if application.status in [
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED,
                ApplicationStatus.CANCELLED,
            ]:

                return Response(
                    {
                        "detail": (
                            "No workflow action is allowed "
                            "after the application is finalized."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # 5. Draft application cannot be approved
            # ------------------------------------------------

            if application.status == ApplicationStatus.DRAFT:

                return Response(
                    {
                        "detail": (
                            "Draft application must be "
                            "submitted before approval."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # 6. Revision required
            # ------------------------------------------------

            if (
                application.status
                == ApplicationStatus.REVISION_REQUIRED
            ):

                return Response(
                    {
                        "detail": (
                            "The application is waiting "
                            "for revision from the student."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # 7. Check current workflow step
            # ------------------------------------------------

            if not application.current_step_id:

                return Response(
                    {
                        "detail": (
                            "Application has no current "
                            "workflow step."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:

                current_step = (
                    WorkflowStep.objects
                    .select_related(
                        "workflow",
                        "office"
                    )
                    .get(
                        pk=application.current_step_id
                    )
                )

            except WorkflowStep.DoesNotExist:

                return Response(
                    {
                        "detail": (
                            "Current workflow step "
                            "does not exist."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # 8. Validate workflow and office
            # ------------------------------------------------

            if not application.workflow.is_active:

                return Response(
                    {
                        "detail": (
                            "Application workflow is inactive."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                current_step.workflow_id
                != application.workflow_id
            ):

                return Response(
                    {
                        "detail": (
                            "Current step does not belong "
                            "to this application's workflow."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                not current_step.office_id
                or not current_step.office.is_active
            ):

                return Response(
                    {
                        "detail": (
                            "Current workflow step "
                            "has no active office."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # 9. Check officer authorization
            # ------------------------------------------------

            user = request.user

            # Admin override
            authorized = (
                user.user_type == "admin"
            )

            if not authorized:

                authorized = (
                    get_officer_applications(user)
                    .filter(
                        pk=application.pk
                    )
                    .exists()
                )

            # ------------------------------------------------
            # 10. Reject unauthorized officer
            # ------------------------------------------------

            if not authorized:

                return Response(
                    {
                        "detail": (
                            "You are not authorized to "
                            "perform this action at the "
                            "current workflow step."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # ------------------------------------------------
            # 11. Check allowed workflow actions
            # ------------------------------------------------

            action_allowed = {

                ActionType.APPROVED:
                    current_step.can_approve,

                ActionType.REJECTED:
                    current_step.can_reject,

                ActionType.REVISION_REQUIRED:
                    current_step.can_request_revision,
            }

            if not action_allowed[action]:

                return Response(
                    {
                        "detail": (
                            "This action is not "
                            "allowed at this step."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # ------------------------------------------------
            # 12. Create approval log
            # ------------------------------------------------

            approval_log = ApprovalLog.objects.create(

                application=application,

                workflow_step=current_step,

                action_by=user,

                action=action,

                remarks=remarks,
            )

            # ------------------------------------------------
            # 13. REJECTED
            # ------------------------------------------------

            if action == ActionType.REJECTED:

                application.status = (
                    ApplicationStatus.REJECTED
                )

                application.completed_at = (
                    timezone.now()
                )

                application.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "updated_at",
                    ]
                )

                return Response(
                    {
                        "message": (
                            "Application rejected successfully."
                        ),

                        "application_id":
                            application.id,

                        "tracking_number":
                            application.tracking_number,

                        "status":
                            application.status,

                        "current_step":
                            current_step.step_name,

                        "approval_log":
                            ApprovalLogSerializer(
                                approval_log
                            ).data,
                    },
                    status=status.HTTP_200_OK,
                )

            # ------------------------------------------------
            # 14. REVISION REQUIRED
            # ------------------------------------------------

            if action == ActionType.REVISION_REQUIRED:

                application.status = (
                    ApplicationStatus.REVISION_REQUIRED
                )

                application.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                return Response(
                    {
                        "message": (
                            "Revision requested successfully."
                        ),

                        "application_id":
                            application.id,

                        "tracking_number":
                            application.tracking_number,

                        "status":
                            application.status,

                        "current_step":
                            current_step.step_name,

                        "approval_log":
                            ApprovalLogSerializer(
                                approval_log
                            ).data,
                    },
                    status=status.HTTP_200_OK,
                )

            # ------------------------------------------------
            # 15. Find next workflow step
            # ------------------------------------------------

            next_step = (
                application.workflow.steps
                .filter(
                    step_order__gt=(
                        current_step.step_order
                    )
                )
                .select_related("office")
                .order_by("step_order")
                .first()
            )

            # ------------------------------------------------
            # 16. Move to next step
            # ------------------------------------------------

            if next_step:

                application.current_step = next_step

                application.status = (
                    ApplicationStatus.IN_PROGRESS
                )

                application.save(
                    update_fields=[
                        "current_step",
                        "status",
                        "updated_at",
                    ]
                )

                return Response(
                    {
                        "message": (
                            "Application approved and "
                            "forwarded to the next "
                            "workflow step."
                        ),

                        "application_id":
                            application.id,

                        "tracking_number":
                            application.tracking_number,

                        "previous_step":
                            current_step.step_name,

                        "next_step":
                            next_step.step_name,

                        "next_office":
                            next_step.office.name,

                        "status":
                            application.status,

                        "approval_log":
                            ApprovalLogSerializer(
                                approval_log
                            ).data,
                    },
                    status=status.HTTP_200_OK,
                )

            # ------------------------------------------------
            # 17. Final approval
            # ------------------------------------------------

            application.status = (
                ApplicationStatus.APPROVED
            )

            application.completed_at = (
                timezone.now()
            )

            application.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "message": (
                        "Application fully "
                        "approved successfully."
                    ),

                    "application_id":
                        application.id,

                    "tracking_number":
                        application.tracking_number,

                    "status":
                        application.status,

                    "final_step":
                        current_step.step_name,

                    "approval_log":
                        ApprovalLogSerializer(
                            approval_log
                        ).data,
                },
                status=status.HTTP_200_OK,
            )


# =========================================================
# STUDENT APPLICATION RESUBMISSION
# =========================================================

class ApplicationResubmitView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        # Only students can resubmit applications

        if request.user.user_type != "student":

            return Response(
                {
                    "detail":
                    "Only students can resubmit applications."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        allowed_fields = {
            "title",
            "description",
            "form_data",
        }

        unknown_fields = (
            set(request.data.keys()) - allowed_fields
        )

        if unknown_fields:

            return Response(
                {
                    "detail":
                    "Only title, description and "
                    "form_data can be corrected."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ApplicationResubmitSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        with transaction.atomic():

            try:

                application = (
                    Application.objects
                    .select_for_update()
                    .get(pk=pk)
                )

            except Application.DoesNotExist:

                return Response(
                    {
                        "detail":
                        "Application not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check application ownership

            if application.student.user_id != request.user.id:

                return Response(
                    {
                        "detail":
                        "You cannot resubmit "
                        "another student's application."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # Only revision-required applications
            # can be resubmitted

            if application.status != (
                ApplicationStatus.REVISION_REQUIRED
            ):

                return Response(
                    {
                        "detail":
                        "Only applications requiring "
                        "revision can be resubmitted."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not application.current_step_id:

                return Response(
                    {
                        "detail":
                        "Application has no current workflow step."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Apply corrected data

            data = serializer.validated_data

            if "title" in data:

                application.title = data["title"]

            if "description" in data:

                application.description = (
                    data["description"]
                )

            if "form_data" in data:

                application.form_data = (
                    data["form_data"]
                )

            # Application becomes actionable again

            application.status = (
                ApplicationStatus.IN_PROGRESS
            )

            # Do not reset current_step.
            # Return to the same officer.

            application.save(
                update_fields=[
                    "title",
                    "description",
                    "form_data",
                    "status",
                    "updated_at",
                ]
            )

            # Record resubmission in approval history

            ApprovalLog.objects.create(
                application=application,
                workflow_step=application.current_step,
                action_by=request.user,
                action=ActionType.RESUBMITTED,
                remarks=(
                    "Student resubmitted "
                    "the corrected application."
                ),
            )

            return Response(
                {
                    "message":
                    "Application resubmitted successfully.",

                    "application_id":
                    application.id,

                    "tracking_number":
                    application.tracking_number,

                    "status":
                    application.status,

                    "current_step":
                    application.current_step.step_name,
                },
                status=status.HTTP_200_OK
            )


# =========================================================
# APPLICATION TRACKING
# =========================================================

class ApplicationTrackingView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        user = request.user

        # ---------------------------------------------
        # 1. Application access
        # ---------------------------------------------

        if user.user_type == "admin":

            application = get_object_or_404(
                Application.objects.select_related(
                    "student",
                    "student__user",
                    "student__program",
                    "student__program__department",
                    "student__batch",
                    "application_type",
                    "workflow",
                    "current_step",
                    "current_step__office",
                ),
                pk=pk,
            )

        elif user.user_type == "student":

            application = get_object_or_404(
                Application.objects.select_related(
                    "student",
                    "student__user",
                    "student__program",
                    "student__program__department",
                    "student__batch",
                    "application_type",
                    "workflow",
                    "current_step",
                    "current_step__office",
                ),
                pk=pk,
                student__user=user,
            )

        else:

            return Response(
                {
                    "detail":
                    "Only the student who owns the application "
                    "or an admin can track it."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ---------------------------------------------
        # 2. Decide where application currently is
        # ---------------------------------------------

        current_holder = None
        current_officer = None

        if application.status == ApplicationStatus.REVISION_REQUIRED:

            current_holder = "student"

        elif application.status in [
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.CANCELLED,
        ]:

            current_holder = "completed"

        elif application.current_step:

            current_holder = "officer"

            today = timezone.localdate()

            assignments = (
                ResponsibilityAssignment.objects
                .filter(
                    responsibility_type=(
                        application.current_step.required_responsibility
                    ),
                    office=application.current_step.office,
                    is_active=True,
                    start_date__lte=today,
                )
                .filter(
                    Q(end_date__isnull=True) |
                    Q(end_date__gte=today)
                )
            )

            # -----------------------------------------
            # Advisor -> exact student batch
            # -----------------------------------------

            if (
                application.current_step.required_responsibility
                == "advisor"
            ):

                assignments = assignments.filter(
                    batch=application.student.batch
                )

                if application.student.program.department_id:

                    assignments = assignments.filter(
                        Q(department__isnull=True) |
                        Q(
                            department=(
                                application.student.program.department
                            )
                        )
                    )

            # -----------------------------------------
            # HOD -> exact student department
            # -----------------------------------------

            elif (
                application.current_step.required_responsibility
                == "hod"
            ):

                assignments = assignments.filter(
                    department=(
                        application.student.program.department
                    )
                )

            assignment = (
                assignments
                .select_related(
                    "faculty",
                    "faculty__user",
                    "staff",
                    "staff__user",
                    "office",
                )
                .first()
            )

            # -----------------------------------------
            # 3. Current officer information
            # -----------------------------------------

            if assignment:

                person_profile = (
                    assignment.faculty
                    if assignment.faculty
                    else assignment.staff
                )

                officer_user = person_profile.user

                profile_picture = None

                if officer_user.profile_picture:

                    profile_picture = request.build_absolute_uri(
                        officer_user.profile_picture.url
                    )

                current_officer = {
                    "id": officer_user.id,

                    "name": (
                        officer_user.get_full_name()
                        or officer_user.username
                    ),

                    "email": officer_user.email,

                    "profile_picture": profile_picture,

                    "designation": (
                        person_profile.designation
                    ),

                    "responsibility": (
                        assignment.get_responsibility_type_display()
                    ),

                    "responsibility_code": (
                        assignment.responsibility_type
                    ),

                    "office": (
                        assignment.office.name
                        if assignment.office
                        else None
                    ),

                    "office_location": (
                        assignment.office.office_location
                        if assignment.office
                        else None
                    ),

                    "office_email": (
                        assignment.office.email
                        if assignment.office
                        else None
                    ),
                }

        # ---------------------------------------------
        # 4. Approval / status history
        # ---------------------------------------------

        history = []
        approval_stamps = []

        approval_logs = (
            application.approval_logs
            .select_related(
                "workflow_step",
                "workflow_step__office",
                "action_by",
            )
            .order_by("action_date")
        )

        for log in approval_logs:

            action_user = log.action_by

            designation = None
            profile_picture = None

            faculty_profile = getattr(
                action_user,
                "faculty_profile",
                None
            )

            staff_profile = getattr(
                action_user,
                "staff_profile",
                None
            )

            if faculty_profile:
                designation = faculty_profile.designation

            elif staff_profile:
                designation = staff_profile.designation

            elif action_user.user_type == "admin":
                designation = "Administrator"

            elif action_user.user_type == "student":
                designation = "Student"

            if action_user.profile_picture:

                profile_picture = request.build_absolute_uri(
                    action_user.profile_picture.url
                )

            history.append({
                "id": log.id,

                "step": log.workflow_step.step_name,

                "responsibility": (
                    log.workflow_step.required_responsibility
                ),

                "action": log.action,

                "action_by": (
                    action_user.get_full_name()
                    or action_user.username
                ),

                "designation": designation,

                "profile_picture": profile_picture,

                "remarks": log.remarks,

                "action_date": log.action_date,
            })

        # -----------------------------------------
        # Electronic approval stamp
        # -----------------------------------------

            if log.action == ActionType.APPROVED:
                responsibility = None
            if log.workflow_step.required_responsibility:
                responsibility = (
                    log.workflow_step.get_required_responsibility_display()
                )
                office = log.workflow_step.office
                approval_stamps.append({
                    "approval_log_id": log.id,
                    "step": log.workflow_step.step_name,
                    "approved_by": (
                        action_user.get_full_name()
                        or action_user.username
                        ),

        "designation":
            designation,

        "responsibility":
            responsibility,

        "email":
            action_user.email,

        "profile_picture":
            profile_picture,

        "office": (
            office.name
            if office
            else None
        ),

        "office_location": (
            office.office_location
            if office
            else None
        ),

        "approved_at":
            log.action_date,

        "remarks":
            log.remarks,

        "verification_type":
            "authenticated_account_action",

        "verification_text":
            "Electronically approved through IntelliCampus",
    })

        # ---------------------------------------------
        # 5. Final response
        # ---------------------------------------------

        return Response(
            {
                "application": {
                    "id": application.id,

                    "tracking_number":
                        application.tracking_number,

                    "application_type":
                        application.application_type.name,

                    "title":
                        application.title,

                    "description":
                        application.description,

                    "status":
                        application.status,

                    "priority":
                        application.priority,

                    "current_step": (
                        application.current_step.step_name
                        if application.current_step
                        else None
                    ),

                    "submitted_at":
                        application.submitted_at,

                    "completed_at":
                        application.completed_at,
                },

                "student": {
                    "name": (
                        application.student.user.get_full_name()
                        or application.student.user.username
                    ),

                    "registration_number":
                        application.student.registration_number,

                    "program":
                        application.student.program.name,

                    "batch":
                        application.student.batch.name,
                },

                "current_holder":
                    current_holder,

                "current_officer":
                    current_officer,

                "history":
                    history,

                "approval_stamps": approval_stamps,
            },
            status=status.HTTP_200_OK,
        )