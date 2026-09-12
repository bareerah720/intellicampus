from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from accounts.models import (
    User,
    StudentProfile,
    Office,
)


# =========================================================
# APPLICATION TYPE
# =========================================================

class ApplicationType(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        related_name="application_types"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Application Type"
        verbose_name_plural = "Application Types"

    def __str__(self):
        return self.name


# =========================================================
# APPLICATION FIELD
# =========================================================

class FieldType(models.TextChoices):
    TEXT = "text", "Text"
    TEXTAREA = "textarea", "Textarea"
    NUMBER = "number", "Number"
    EMAIL = "email", "Email"
    DATE = "date", "Date"
    DROPDOWN = "dropdown", "Dropdown"
    RADIO = "radio", "Radio"
    CHECKBOX = "checkbox", "Checkbox"
    FILE = "file", "File"


class ApplicationField(models.Model):

    application_type = models.ForeignKey(
        ApplicationType,
        on_delete=models.CASCADE,
        related_name="fields"
    )

    label = models.CharField(
        max_length=100
    )

    field_name = models.CharField(
        max_length=100
    )

    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices
    )

    placeholder = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    is_required = models.BooleanField(
        default=False
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["display_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["application_type", "field_name"],
                name="unique_field_name_per_application_type"
            )
        ]

    def __str__(self):
        return f"{self.application_type.name} - {self.label}"


# =========================================================
# APPLICATION FIELD OPTION
# =========================================================

class ApplicationFieldOption(models.Model):

    field = models.ForeignKey(
        ApplicationField,
        on_delete=models.CASCADE,
        related_name="options"
    )

    label = models.CharField(
        max_length=100
    )

    value = models.CharField(
        max_length=100
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["field", "value"],
                name="unique_option_value_per_field"
            )
        ]

    def __str__(self):
        return f"{self.field.label} - {self.label}"


# =========================================================
# WORKFLOW
# =========================================================

class Workflow(models.Model):

    application_type = models.ForeignKey(
        ApplicationType,
        on_delete=models.CASCADE,
        related_name="workflows"
    )

    workflow_name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["workflow_name"]

    def __str__(self):
        return f"{self.application_type.name} - {self.workflow_name}"


# =========================================================
# WORKFLOW STEP
# =========================================================

class WorkflowStep(models.Model):

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="steps"
    )

    office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        related_name="workflow_steps"
    )

    step_name = models.CharField(
        max_length=100
    )

    step_order = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    can_approve = models.BooleanField(
        default=True
    )

    can_reject = models.BooleanField(
        default=True
    )

    can_request_revision = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["step_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "step_order"],
                name="unique_step_order_per_workflow"
            )
        ]

    def __str__(self):
        return f"{self.workflow.workflow_name} - Step {self.step_order}: {self.step_name}"


# =========================================================
# APPLICATION
# =========================================================

class ApplicationStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    IN_PROGRESS = "in_progress", "In Progress"
    REVISION_REQUIRED = "revision_required", "Revision Required"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CANCELLED = "cancelled", "Cancelled"


class ApplicationPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class Application(models.Model):

    tracking_number = models.CharField(
        max_length=30,
        unique=True,
        blank=True
    )

    application_type = models.ForeignKey(
        ApplicationType,
        on_delete=models.PROTECT,
        related_name="applications"
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="applications"
    )

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.PROTECT,
        related_name="applications"
    )

    current_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.PROTECT,
        related_name="current_applications",
        blank=True,
        null=True
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    # Stores values submitted through dynamic application fields
    form_data = models.JSONField(
        default=dict,
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT
    )

    priority = models.CharField(
        max_length=20,
        choices=ApplicationPriority.choices,
        default=ApplicationPriority.MEDIUM
    )

    ai_priority_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    submitted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Application"
        verbose_name_plural = "Applications"

    def save(self, *args, **kwargs):

        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()

        self.full_clean()
        super().save(*args, **kwargs)

    def generate_tracking_number(self):

        last_application = (
            Application.objects
            .order_by("-id")
            .first()
        )

        if last_application:
            next_id = last_application.id + 1
        else:
            next_id = 1

        return f"APP-{next_id:06d}"

    def clean(self):

        if self.current_step:
            if self.current_step.workflow_id != self.workflow_id:
                raise ValidationError(
                    "Current step must belong to the selected workflow."
                )

        if (
            self.workflow_id
            and self.application_type_id
            and self.workflow.application_type_id != self.application_type_id
        ):
            raise ValidationError(
                "Selected workflow must belong to the selected application type."
            )

        if self.ai_priority_score is not None:
            if self.ai_priority_score < 0 or self.ai_priority_score > 100:
                raise ValidationError(
                    "AI priority score must be between 0 and 100."
                )

    def __str__(self):
        return f"{self.tracking_number} - {self.title}"


# =========================================================
# ATTACHMENT
# =========================================================

class Attachment(models.Model):

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="attachments"
    )

    file_name = models.CharField(
        max_length=255
    )

    file_path = models.FileField(
        upload_to="application_attachments/"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="application_attachments"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.file_name


# =========================================================
# COMMENT
# =========================================================

class Comment(models.Model):

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="application_comments"
    )

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user.username}"


# =========================================================
# APPROVAL LOG
# =========================================================

class ActionType(models.TextChoices):
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    FORWARDED = "forwarded", "Forwarded"
    REVISION_REQUIRED = "revision_required", "Revision Required"


class ApprovalLog(models.Model):

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="approval_logs"
    )

    workflow_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.PROTECT,
        related_name="approval_logs"
    )

    action_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="approval_actions"
    )

    action = models.CharField(
        max_length=30,
        choices=ActionType.choices
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    action_date = models.DateTimeField(
        auto_now_add=True
    )

    def clean(self):

        if (
            self.application_id
            and self.workflow_step_id
            and self.workflow_step.workflow_id != self.application.workflow_id
        ):
            raise ValidationError(
                "Workflow step must belong to the application's workflow."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.application.tracking_number} - "
            f"{self.get_action_display()}"
        )