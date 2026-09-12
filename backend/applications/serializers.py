from urllib import request

from rest_framework import serializers

from accounts.models import StudentProfile
from django.utils import timezone

from .models import (
    ApplicationType,
    ApplicationField,
    ApplicationFieldOption,
    Workflow,
    WorkflowStep,
    ApplicationStatus,
    StudentProfile, 
    Application,
    Attachment,
    Comment,
    ApprovalLog,
)
from accounts.models import StudentProfile

# =========================================================
# APPLICATION TYPE SERIALIZER
# =========================================================

class ApplicationTypeSerializer(serializers.ModelSerializer):

    office_name = serializers.CharField(
        source="office.name",
        read_only=True
    )

    class Meta:
        model = ApplicationType

        fields = [
            "id",
            "name",
            "description",
            "office",
            "office_name",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "office_name",
            "created_at",
            "updated_at",
        ]


# =========================================================
# APPLICATION FIELD SERIALIZER
# =========================================================

class ApplicationFieldSerializer(serializers.ModelSerializer):

    application_type_name = serializers.CharField(
        source="application_type.name",
        read_only=True
    )

    class Meta:
        model = ApplicationField

        fields = [
            "id",
            "application_type",
            "application_type_name",
            "label",
            "field_name",
            "field_type",
            "placeholder",
            "is_required",
            "display_order",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "application_type_name",
            "created_at",
            "updated_at",
        ]


# =========================================================
# APPLICATION FIELD OPTION SERIALIZER
# =========================================================

class ApplicationFieldOptionSerializer(serializers.ModelSerializer):

    field_name = serializers.CharField(
        source="field.label",
        read_only=True
    )

    class Meta:
        model = ApplicationFieldOption

        fields = [
            "id",
            "field",
            "field_name",
            "label",
            "value",
        ]

        read_only_fields = [
            "id",
            "field_name",
        ]


# =========================================================
# WORKFLOW STEP SERIALIZER
# =========================================================

class WorkflowStepSerializer(serializers.ModelSerializer):

    workflow_name = serializers.CharField(
        source="workflow.workflow_name",
        read_only=True
    )

    office_name = serializers.CharField(
        source="office.name",
        read_only=True
    )

    class Meta:
        model = WorkflowStep

        fields = [
            "id",
            "workflow",
            "workflow_name",
            "office",
            "office_name",
            "step_name",
            "step_order",
            "can_approve",
            "can_reject",
            "can_request_revision",
        ]

        read_only_fields = [
            "id",
            "workflow_name",
            "office_name",
        ]


# =========================================================
# WORKFLOW SERIALIZER
# =========================================================

class WorkflowSerializer(serializers.ModelSerializer):

    application_type_name = serializers.CharField(
        source="application_type.name",
        read_only=True
    )

    steps = WorkflowStepSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Workflow

        fields = [
            "id",
            "application_type",
            "application_type_name",
            "workflow_name",
            "description",
            "is_active",
            "steps",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "application_type_name",
            "steps",
            "created_at",
            "updated_at",
        ]


# =========================================================
# APPLICATION SERIALIZER
# =========================================================
class ApplicationSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.user.get_full_name",
        read_only=True
    )

    registration_number = serializers.CharField(
        source="student.registration_number",
        read_only=True
    )

    application_type_name = serializers.CharField(
        source="application_type.name",
        read_only=True
    )

    workflow_name = serializers.CharField(
        source="workflow.workflow_name",
        read_only=True
    )

    current_step_name = serializers.CharField(
        source="current_step.step_name",
        read_only=True
    )

    class Meta:
        model = Application

        fields = [
            "id",
            "tracking_number",
            "application_type",
            "application_type_name",
            "student",
            "student_name",
            "registration_number",
            "workflow",
            "workflow_name",
            "current_step",
            "current_step_name",
            "title",
            "description",
            "form_data",
            "status",
            "priority",
            "ai_priority_score",
            "submitted_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "tracking_number",

            # Automatically determined
            "student",
            "workflow",
            "current_step",

            # Display-only
            "student_name",
            "registration_number",
            "application_type_name",
            "workflow_name",
            "current_step_name",

            "ai_priority_score",
            "submitted_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):

        application_type = attrs.get("application_type")

        if not application_type:
            raise serializers.ValidationError({
                "application_type": "Application type is required."
            })

        # Find active workflow for selected application type
        try:
            workflow = Workflow.objects.get(
                application_type=application_type,
                is_active=True
            )
        except Workflow.DoesNotExist:
            raise serializers.ValidationError({
                "application_type": (
                    "No active workflow exists for this "
                    "application type."
                )
            })

        # Find first step of workflow
        current_step = workflow.steps.order_by(
            "step_order"
        ).first()

        if not current_step:
            raise serializers.ValidationError({
                "application_type": (
                    "The selected application type has "
                    "no workflow steps."
                )
            })
         # Store automatically selected objects
        attrs["workflow"] = workflow
        attrs["current_step"] = current_step
        
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
          raise serializers.ValidationError({
            "student": "Authenticated student is required."
        })

        # -------------------------------------------------
        # Get logged-in student's profile
        # -------------------------------------------------

        try:
            student_profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            raise serializers.ValidationError({
                "student": "Student profile does not exist for this user."
            })

        validated_data["student"] = student_profile

        # -------------------------------------------------
        # Automatically submit application
        # -------------------------------------------------

        validated_data["status"] = ApplicationStatus.SUBMITTED
        validated_data["submitted_at"] = timezone.now()
        return super().create(validated_data)

# =========================================================
# ATTACHMENT SERIALIZER
# =========================================================

class AttachmentSerializer(serializers.ModelSerializer):

    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name",
        read_only=True
    )

    application_tracking_number = serializers.CharField(
        source="application.tracking_number",
        read_only=True
    )

    class Meta:
        model = Attachment

        fields = [
            "id",
            "application",
            "application_tracking_number",
            "file_name",
            "file_path",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_at",
        ]

        read_only_fields = [
            "id",
            "application_tracking_number",
            "uploaded_by_name",
            "uploaded_at",
        ]


# =========================================================
# COMMENT SERIALIZER
# =========================================================

class CommentSerializer(serializers.ModelSerializer):

    user_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True
    )

    application_tracking_number = serializers.CharField(
        source="application.tracking_number",
        read_only=True
    )

    class Meta:
        model = Comment

        fields = [
            "id",
            "application",
            "application_tracking_number",
            "user",
            "user_name",
            "comment",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "application_tracking_number",
            "user_name",
            "created_at",
        ]


# =========================================================
# APPROVAL LOG SERIALIZER
# =========================================================

class ApprovalLogSerializer(serializers.ModelSerializer):

    application_tracking_number = serializers.CharField(
        source="application.tracking_number",
        read_only=True
    )

    workflow_step_name = serializers.CharField(
        source="workflow_step.step_name",
        read_only=True
    )

    action_by_name = serializers.CharField(
        source="action_by.get_full_name",
        read_only=True
    )

    class Meta:
        model = ApprovalLog

        fields = [
            "id",
            "application",
            "application_tracking_number",
            "workflow_step",
            "workflow_step_name",
            "action_by",
            "action_by_name",
            "action",
            "remarks",
            "action_date",
        ]

        read_only_fields = [
            "id",
            "application_tracking_number",
            "workflow_step_name",
            "action_by_name",
            "action_by",
            "action_date",
        ]