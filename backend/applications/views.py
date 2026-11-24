
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ResponsibilityAssignment, StudentProfile, User
from accounts.models import UserType
from accounts.permissions import IsAdmin, IsAdminOrReadOnly

from notifications.models import Notification
from notifications.services import notify_student, notify_current_officers

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
    validate_dynamic_form_data,
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
        condition = Q(current_step__office_id=assignment.office_id) & (
            Q(current_step__required_responsibility=assignment.responsibility_type)
            | Q(current_step__required_responsibility__isnull=True)
            | Q(current_step__required_responsibility="")
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

    @transaction.atomic
    def perform_create(self, serializer):

        if self.request.user.user_type != "student":

            raise PermissionDenied(
                "Only students can submit applications."
            )

        application = serializer.save()

        notify_student(
            application,
            "Application Submitted",
            f"Your application {application.tracking_number} has been submitted successfully.",
            Notification.NotificationType.APPLICATION_SUBMITTED,
        )

        notify_current_officers(
            application,
            "New Application Received",
            f"A new application {application.tracking_number} is waiting for your review.",
            Notification.NotificationType.APPLICATION_SUBMITTED,
        )


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

        if instance.application.status in [
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.CANCELLED,
        ]:
            raise PermissionDenied(
                "Attachments of a finalized application "
                "cannot be deleted."
            )

        # Admin can delete
        if user.user_type == "admin":
            instance.delete()
            return

        # Only original uploader can delete
        if instance.uploaded_by_id != user.id:

            raise PermissionDenied(
                "You cannot delete another user's attachment."
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

        if accessible_application.status in [
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.CANCELLED,
        ]:
            raise PermissionDenied(
                "Comments cannot be added to a finalized application."
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

class AdminAnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        active_students = StudentProfile.objects.filter(
            is_active=True,
            user__is_active=True,
        )

        department_rows = (
            active_students
            .filter(program__department__isnull=False)
            .values(
                "program__department_id",
                "program__department__name",
            )
            .annotate(count=Count("id"))
            .order_by("program__department__name")
        )
        department_distribution = [
            {
                "department": row["program__department__name"],
                "count": row["count"],
            }
            for row in department_rows
        ]

        missing_department_count = active_students.filter(
            program__department__isnull=True
        ).count()
        if missing_department_count:
            department_distribution.append({
                "department": "Unassigned",
                "count": missing_department_count,
            })

        semester_rows = (
            active_students
            .filter(current_semester__isnull=False)
            .values(
                "current_semester__number",
                "current_semester__title",
            )
            .annotate(count=Count("id"))
            .order_by("current_semester__number")
        )
        semester_distribution = [
            {
                "semester": row["current_semester__title"],
                "number": row["current_semester__number"],
                "count": row["count"],
            }
            for row in semester_rows
        ]

        missing_semester_count = active_students.filter(
            current_semester__isnull=True
        ).count()
        if missing_semester_count:
            semester_distribution.append({
                "semester": "Unassigned",
                "number": None,
                "count": missing_semester_count,
            })

        status_breakdown = {
            "submitted": Application.objects.filter(status=ApplicationStatus.SUBMITTED).count(),
            "in_progress": Application.objects.filter(status=ApplicationStatus.IN_PROGRESS).count(),
            "approved": Application.objects.filter(status=ApplicationStatus.APPROVED).count(),
            "rejected": Application.objects.filter(status=ApplicationStatus.REJECTED).count(),
            "revision_required": Application.objects.filter(status=ApplicationStatus.REVISION_REQUIRED).count(),
        }

        type_rows = (
            Application.objects
            .values("application_type_id", "application_type__name")
            .annotate(count=Count("id"))
            .order_by("application_type__name")
        )
        application_types = [
            {
                "application_type": row["application_type__name"],
                "count": row["count"],
            }
            for row in type_rows
        ]

        submission_rows = (
            Application.objects
            .exclude(submitted_at__isnull=True)
            .annotate(month=TruncMonth("submitted_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        monthly_submissions = self.fill_missing_months([
            {"month": row["month"].strftime("%Y-%m"), "count": row["count"]}
            for row in submission_rows
            if row["month"]
        ])

        completion_rows = (
            Application.objects
            .exclude(completed_at__isnull=True)
            .annotate(month=TruncMonth("completed_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        monthly_completions = self.fill_missing_months([
            {"month": row["month"].strftime("%Y-%m"), "count": row["count"]}
            for row in completion_rows
            if row["month"]
        ])

        return Response({
            "totals": {
                "students": active_students.count(),
                "faculty": User.objects.filter(
                    user_type=UserType.FACULTY,
                    is_active=True,
                ).count(),
                "staff": User.objects.filter(
                    user_type=UserType.STAFF,
                    is_active=True,
                ).count(),
                "applications": Application.objects.count(),
            },
            "department_distribution": department_distribution,
            "semester_distribution": semester_distribution,
            "application_status": status_breakdown,
            "application_types": application_types,
            "monthly_submissions": monthly_submissions,
            "monthly_completions": monthly_completions,
            "forecast": self.build_submission_forecast(monthly_submissions),
        })

    @staticmethod
    def fill_missing_months(monthly_counts):
        if not monthly_counts:
            return []

        from datetime import datetime

        parsed_months = {
            item["month"]: datetime.strptime(item["month"], "%Y-%m")
            for item in monthly_counts
        }
        counts_by_month = {
            item["month"]: item["count"]
            for item in monthly_counts
        }
        month_indexes = [
            month.year * 12 + month.month - 1
            for month in parsed_months.values()
        ]
        first_month = min(month_indexes)
        last_month = max(month_indexes)

        return [
            {
                "month": f"{month_index // 12:04d}-{month_index % 12 + 1:02d}",
                "count": counts_by_month.get(
                    f"{month_index // 12:04d}-{month_index % 12 + 1:02d}",
                    0,
                ),
            }
            for month_index in range(first_month, last_month + 1)
        ]

    @staticmethod
    def build_submission_forecast(monthly_submissions):
        actual = AdminAnalyticsView.fill_missing_months(monthly_submissions)
        active_months = sum(1 for item in actual if item["count"] > 0)
        if len(actual) < 6 or active_months < 3:
            return {
                "available": False,
                "period": "Next 3 months",
                "message": (
                    "At least six months of submission history with activity "
                    "in three or more months is required."
                ),
                "actual": actual,
                "predicted": [],
            }

        from datetime import datetime

        points = [(index, item["count"]) for index, item in enumerate(actual)]
        count = len(points)
        mean_x = sum(x for x, _ in points) / count
        mean_y = sum(y for _, y in points) / count
        denominator = sum((x - mean_x) ** 2 for x, _ in points)
        slope = (
            sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator
            if denominator
            else 0
        )
        intercept = mean_y - slope * mean_x

        last_month = datetime.strptime(actual[-1]["month"], "%Y-%m")
        year = last_month.year
        month = last_month.month
        predicted = []

        for offset in range(1, 4):
            month += 1
            if month > 12:
                month = 1
                year += 1
            value = max(
                0,
                round(intercept + slope * (count - 1 + offset)),
            )
            predicted.append({
                "month": f"{year:04d}-{month:02d}",
                "count": value,
            })

        return {
            "available": True,
            "period": "Next 3 months",
            "method": "Simple linear trend",
            "disclaimer": "Predictions are estimates, not guaranteed outcomes.",
            "actual": actual,
            "predicted": predicted,
        }


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
        if remarks is None:
            remarks = ""
        if not isinstance(remarks, str):
            return Response(
                {"detail": "Remarks must be text."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        if action in (ActionType.REJECTED, ActionType.REVISION_REQUIRED) and not remarks.strip():
            return Response(
                {"detail": "Remarks are required for rejection or revision requests."},
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


                notify_student(
                    application,
                    "Application Rejected",
                    f"Your application {application.tracking_number} has been rejected. Remarks: {remarks or 'No remarks provided.'}",
                    Notification.NotificationType.APPLICATION_REJECTED,
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


                notify_student(
                    application,
                    "Revision Required",
                    f"Your application {application.tracking_number} requires revision. Remarks: {remarks or 'Please review and correct your application.'}",
                    Notification.NotificationType.REVISION_REQUIRED,
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


                notify_student(
                    application,
                    "Application Forwarded",
                    f"Your application {application.tracking_number} has been approved at {current_step.step_name} and forwarded to {next_step.step_name}.",
                    Notification.NotificationType.APPLICATION_FORWARDED,
                )

                notify_current_officers(
                    application,
                    "Application Forwarded to Your Office",
                    f"Application {application.tracking_number} is now waiting for your review.",
                    Notification.NotificationType.APPLICATION_FORWARDED,
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


            notify_student(
                application,
                "Application Approved",
                f"Congratulations! Your application {application.tracking_number} has been fully approved.",
                Notification.NotificationType.APPLICATION_APPROVED,
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

            serializer = ApplicationResubmitSerializer(
                data=request.data,
                context={"application_type": application.application_type},
            )
            serializer.is_valid(raise_exception=True)

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


            notify_student(
                application,
                "Application Resubmitted",
                f"Your corrected application {application.tracking_number} has been resubmitted successfully.",
                Notification.NotificationType.APPLICATION_RESUBMITTED,
            )

            notify_current_officers(
                application,
                "Application Resubmitted",
                f"Corrected application {application.tracking_number} is waiting for your review.",
                Notification.NotificationType.APPLICATION_RESUBMITTED,
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

        elif user.user_type in ("faculty", "staff"):
            application = get_object_or_404(
                get_officer_applications(user).select_related(
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

        else:

            return Response(
                {
                    "detail":
                    "Only the student who owns the application, "
                    "an assigned officer, or an admin can track it."
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
                    office=application.current_step.office,
                    is_active=True,
                    start_date__lte=today,
                )
                .filter(
                    Q(end_date__isnull=True) |
                    Q(end_date__gte=today)
                )
            )

            if application.current_step.required_responsibility:
                assignments = assignments.filter(
                    responsibility_type=(
                        application.current_step.required_responsibility
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

                    "office_contact_number": (
                        assignment.office.contact_number
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
                responsibility = (
                    log.workflow_step.get_required_responsibility_display()
                    if log.workflow_step.required_responsibility
                    else "Authorized officer"
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
