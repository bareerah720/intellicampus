from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import IsAdminOrReadOnly
from rest_framework.exceptions import PermissionDenied

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
    CommentSerializer,
    ApprovalLogSerializer,
)
from accounts.models import ResponsibilityAssignment


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

class ApplicationListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = ApplicationSerializer

    permission_classes = [IsAuthenticated]

    queryset = Application.objects.all()

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

        # Faculty/staff visibility will be handled
        # through their scoped responsibility assignments.
        return Application.objects.none()

    def perform_create(self, serializer):

        if self.request.user.user_type != "student":

            raise PermissionDenied(
                "Only students can submit applications."
            )

        serializer.save()


class ApplicationDetailView(
    generics.RetrieveAPIView
):

    serializer_class = ApplicationSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        if user.user_type == "admin":

            return Application.objects.all()

        if user.user_type == "student":

            return Application.objects.filter(
                student__user=user
            )

        return Application.objects.none()


class AttachmentListCreateView(generics.ListCreateAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]


class AttachmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]


class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]


class ApprovalLogListCreateView(generics.ListAPIView):
    queryset = ApprovalLog.objects.all()
    serializer_class = ApprovalLogSerializer
    permission_classes = [IsAuthenticated]


class ApprovalLogDetailView(generics.RetrieveAPIView):
    queryset = ApprovalLog.objects.all()
    serializer_class = ApprovalLogSerializer
    permission_classes = [IsAuthenticated]

# =========================================================
# OFFICER APPLICATION ACCESS
# =========================================================

def get_officer_applications(user):

    # Only faculty and staff can use officer inbox
    if user.user_type not in ["faculty", "staff"]:
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

    # Start with an empty filter
    application_filter = Q(pk__in=[])

    for assignment in assignments:

        # Application must currently be at assigned office
        condition = Q(
            current_step__office_id=assignment.office_id
        )

        # Match department if assignment is department-specific
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

    # Return applications awaiting officer action
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
# OFFICER INBOX VIEW
# =========================================================

class OfficerInboxView(generics.ListAPIView):

    serializer_class = ApplicationSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        if user.user_type == "admin":

            return Application.objects.filter(
                status__in=[
                    ApplicationStatus.SUBMITTED,
                    ApplicationStatus.IN_PROGRESS,
                ]
            )

        return get_officer_applications(user)

class ApplicationActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        # ----------------------------------------------------
        # 1. Get action and remarks from request
        # ----------------------------------------------------
        action = request.data.get("action")
        remarks = request.data.get("remarks", "")

        valid_actions = [
            ActionType.APPROVED,
            ActionType.REJECTED,
            ActionType.REVISION_REQUIRED,
        ]

        # ----------------------------------------------------
        # 2. Validate action
        # ----------------------------------------------------
        if action not in valid_actions:
            return Response(
                {
                    "detail": (
                        "Invalid action. "
                        "Use approved, rejected, or revision_required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # 3. Start database transaction
        # ----------------------------------------------------
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
                    {"detail": "Application not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ------------------------------------------------
            # 4. Final applications cannot be changed
            # ------------------------------------------------
            if application.status in [
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED,
                ApplicationStatus.CANCELLED,
            ]:
                return Response(
                    {
                        "detail": (
                            "No workflow action is allowed after "
                            "the application is finalized."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # 5. Application waiting for revision cannot
            #    receive another officer action
            # ------------------------------------------------
            if application.status == ApplicationStatus.REVISION_REQUIRED:
                return Response(
                    {
                        "detail": (
                            "The application is waiting for revision "
                            "from the student."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # 6. Check current workflow step
            # ------------------------------------------------
            if not application.current_step_id:
                return Response(
                    {
                        "detail": (
                            "Application has no current workflow step."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch current step separately.
            # This avoids select_for_update problems with nullable relations.
            try:
                current_step = (
                    WorkflowStep.objects
                    .select_related("workflow", "office")
                    .get(pk=application.current_step_id)
                )

            except WorkflowStep.DoesNotExist:
                return Response(
                    {
                        "detail": (
                            "Current workflow step does not exist."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # 7. Validate workflow and office
            # ------------------------------------------------
            if not application.workflow.is_active:
                return Response(
                    {"detail": "Application workflow is inactive."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if current_step.workflow_id != application.workflow_id:
                return Response(
                    {
                        "detail": (
                            "Current step does not belong to "
                            "this application's workflow."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not current_step.office_id:
                return Response(
                    {
                        "detail": (
                            "No office is assigned to the current step."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not current_step.office.is_active:
                return Response(
                    {
                        "detail": (
                            "The office assigned to the current step "
                            "is inactive."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # 8. Check whether current user is authorized
            # ------------------------------------------------
            user = request.user
            authorized = user.user_type == "admin"
            
            if not authorized:
                authorized = (
                get_officer_applications(user)
                .filter(pk=application.pk)
                .exists()
                )

            if not authorized:

                today = timezone.localdate()

                # Find active responsibility assignments
                active_assignments = (
                    ResponsibilityAssignment.objects
                    .filter(
                        office=current_step.office,
                        is_active=True,
                        start_date__lte=today,
                    )
                    .filter(
                        Q(end_date__isnull=True) |
                        Q(end_date__gte=today)
                    )
                )

                faculty_profile = getattr(
                    user,
                    "faculty_profile",
                    None
                )

                staff_profile = getattr(
                    user,
                    "staff_profile",
                    None
                )

                # Check faculty assignment
                if faculty_profile:
                    authorized = active_assignments.filter(
                        faculty=faculty_profile
                    ).exists()

                # Check staff assignment
                if not authorized and staff_profile:
                    authorized = active_assignments.filter(
                        staff=staff_profile
                    ).exists()

            # ------------------------------------------------
            # 9. Stop unauthorized user
            # ------------------------------------------------
            if not authorized:
                return Response(
                    {
                        "detail": (
                            "You are not authorized to perform "
                            "this action at the current workflow step."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # ------------------------------------------------
            # 10. Check permissions of this workflow step
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
                            "This action is not allowed "
                            "at this workflow step."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # ------------------------------------------------
            # 11. Save action in ApprovalLog
            # ------------------------------------------------
            approval_log = ApprovalLog.objects.create(
                application=application,
                workflow_step=current_step,
                action_by=user,
                action=action,
                remarks=remarks,
            )

            # ------------------------------------------------
            # 12. REJECTED
            # ------------------------------------------------
            if action == ActionType.REJECTED:

                application.status = ApplicationStatus.REJECTED
                application.completed_at = timezone.now()

                application.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "updated_at",
                    ]
                )

                return Response(
                    {
                        "message": "Application rejected successfully.",
                        "application_id": application.id,
                        "tracking_number": application.tracking_number,
                        "status": application.status,
                        "current_step": current_step.step_name,
                        "approval_log":
                            ApprovalLogSerializer(
                                approval_log
                            ).data,
                    },
                    status=status.HTTP_200_OK,
                )

            # ------------------------------------------------
            # 13. REVISION REQUIRED
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
                        "application_id": application.id,
                        "tracking_number":
                            application.tracking_number,
                        "status": application.status,
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
            # 14. APPROVED:
            #     Find next workflow step
            # ------------------------------------------------

            # IMPORTANT:
            # Do NOT use step_order + 1.
            #
            # Example:
            # current = 1
            # next = 3
            #
            # step_order + 1 searches for 2 and would fail.
            next_step = (
                application.workflow.steps
                .filter(
                    step_order__gt=current_step.step_order
                )
                .select_related("office")
                .order_by("step_order")
                .first()
            )

            # ------------------------------------------------
            # 15. Move to next step
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
                            "Application approved and forwarded "
                            "to the next workflow step."
                        ),
                        "application_id": application.id,
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
            # 16. No next step = fully approved
            # ------------------------------------------------
            application.status = ApplicationStatus.APPROVED
            application.completed_at = timezone.now()

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
                        "Application fully approved successfully."
                    ),
                    "application_id": application.id,
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


        if application.status == ApplicationStatus.DRAFT:
            return Response(
        {
            "detail":
                "Draft application must be submitted before approval."
        },
        status=status.HTTP_400_BAD_REQUEST,
    )