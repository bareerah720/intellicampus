from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
    permission_classes = [IsAuthenticated]


class ApplicationTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ApplicationType.objects.all()
    serializer_class = ApplicationTypeSerializer
    permission_classes = [IsAuthenticated]


class ApplicationFieldListCreateView(generics.ListCreateAPIView):
    queryset = ApplicationField.objects.all()
    serializer_class = ApplicationFieldSerializer
    permission_classes = [IsAuthenticated]


class ApplicationFieldDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ApplicationField.objects.all()
    serializer_class = ApplicationFieldSerializer
    permission_classes = [IsAuthenticated]


class ApplicationFieldOptionListCreateView(generics.ListCreateAPIView):
    queryset = ApplicationFieldOption.objects.all()
    serializer_class = ApplicationFieldOptionSerializer
    permission_classes = [IsAuthenticated]


class ApplicationFieldOptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ApplicationFieldOption.objects.all()
    serializer_class = ApplicationFieldOptionSerializer
    permission_classes = [IsAuthenticated]


class WorkflowListCreateView(generics.ListCreateAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]


class WorkflowDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]


class WorkflowStepListCreateView(generics.ListCreateAPIView):
    queryset = WorkflowStep.objects.all()
    serializer_class = WorkflowStepSerializer
    permission_classes = [IsAuthenticated]


class WorkflowStepDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WorkflowStep.objects.all()
    serializer_class = WorkflowStepSerializer
    permission_classes = [IsAuthenticated]


class ApplicationListCreateView(generics.ListCreateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]


class ApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]


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

            # Admin can perform workflow actions
            authorized = user.user_type == "admin"

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