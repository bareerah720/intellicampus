from django.db import transaction
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


class ApprovalLogListCreateView(generics.ListCreateAPIView):
    queryset = ApprovalLog.objects.all()
    serializer_class = ApprovalLogSerializer
    permission_classes = [IsAuthenticated]


class ApprovalLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ApprovalLog.objects.all()
    serializer_class = ApprovalLogSerializer
    permission_classes = [IsAuthenticated]


class ApplicationActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        action = request.data.get("action")
        remarks = request.data.get("remarks", "")
        valid_actions = [
            ActionType.APPROVED,
            ActionType.REJECTED,
            ActionType.REVISION_REQUIRED,
        ]
        if action not in valid_actions:
            return Response(
                {"detail": "Invalid action. Use approved, rejected, or revision_required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                application = (
                    Application.objects.select_for_update()
                    .select_related("workflow", "current_step__office")
                    .get(pk=pk)
                )
            except Application.DoesNotExist:
                return Response(
                    {"detail": "Application not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if application.status in [
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED,
                ApplicationStatus.CANCELLED,
            ]:
                return Response(
                    {"detail": "No workflow action is allowed after the application is finalized."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            current_step = application.current_step
            if not current_step:
                return Response(
                    {"detail": "Application has no current workflow step."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if (
                not application.workflow.is_active
                or current_step.workflow_id != application.workflow_id
                or not current_step.office.is_active
            ):
                return Response(
                    {"detail": "Application has an invalid or inactive current workflow step."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = request.user
            authorized = user.user_type == "admin"
            if not authorized:
                today = timezone.localdate()
                active_assignments = ResponsibilityAssignment.objects.filter(
                    office=current_step.office,
                    is_active=True,
                    start_date__lte=today,
                ).filter(end_date__isnull=True) | ResponsibilityAssignment.objects.filter(
                    office=current_step.office,
                    is_active=True,
                    start_date__lte=today,
                    end_date__gte=today,
                )
                faculty_profile = getattr(user, "faculty_profile", None)
                staff_profile = getattr(user, "staff_profile", None)
                authorized = (
                    active_assignments.filter(faculty=faculty_profile).exists()
                    if faculty_profile else False
                )
                if not authorized and staff_profile:
                    authorized = active_assignments.filter(staff=staff_profile).exists()

            if not authorized:
                return Response(
                    {"detail": "You are not authorized to perform this action at the current workflow step."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            action_allowed = {
                ActionType.APPROVED: current_step.can_approve,
                ActionType.REJECTED: current_step.can_reject,
                ActionType.REVISION_REQUIRED: current_step.can_request_revision,
            }
            if not action_allowed[action]:
                return Response(
                    {"detail": "This action is not allowed at this step."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            ApprovalLog.objects.create(
                application=application,
                workflow_step=current_step,
                action_by=user,
                action=action,
                remarks=remarks,
            )

            if action == ActionType.REJECTED:
                application.status = ApplicationStatus.REJECTED
                application.completed_at = timezone.now()
                application.save(update_fields=["status", "completed_at", "updated_at"])
                return Response({
                    "message": "Application rejected successfully.",
                    "application_id": application.id,
                    "tracking_number": application.tracking_number,
                    "status": application.status,
                    "current_step": current_step.step_name,
                })

            if action == ActionType.REVISION_REQUIRED:
                application.status = ApplicationStatus.REVISION_REQUIRED
                application.save(update_fields=["status", "updated_at"])
                return Response({
                    "message": "Revision requested successfully.",
                    "application_id": application.id,
                    "tracking_number": application.tracking_number,
                    "status": application.status,
                    "current_step": current_step.step_name,
                })

            next_step = application.workflow.steps.filter(
                step_order=current_step.step_order + 1
            ).first()
            if next_step:
                application.current_step = next_step
                application.status = ApplicationStatus.IN_PROGRESS
                application.save(update_fields=["current_step", "status", "updated_at"])
                return Response({
                    "message": "Application approved and forwarded to the next workflow step.",
                    "application_id": application.id,
                    "tracking_number": application.tracking_number,
                    "previous_step": current_step.step_name,
                    "next_step": next_step.step_name,
                    "next_office": next_step.office.name,
                    "status": application.status,
                })

            application.status = ApplicationStatus.APPROVED
            application.completed_at = timezone.now()
            application.save(update_fields=["status", "completed_at", "updated_at"])
            return Response({
                "message": "Application approved successfully.",
                "application_id": application.id,
                "tracking_number": application.tracking_number,
                "status": application.status,
            })
