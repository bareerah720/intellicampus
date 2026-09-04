from django.contrib import admin

from .models import (
    ApplicationType,
    ApplicationField,
    ApplicationFieldOption,
    Workflow,
    WorkflowStep,
    Application,
    Attachment,
    Comment,
    ApprovalLog,
)


# =========================================================
# APPLICATION TYPE
# =========================================================

@admin.register(ApplicationType)
class ApplicationTypeAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "office",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "office",
    )

    search_fields = (
        "name",
        "description",
    )


# =========================================================
# APPLICATION FIELD
# =========================================================

@admin.register(ApplicationField)
class ApplicationFieldAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "application_type",
        "label",
        "field_name",
        "field_type",
        "is_required",
        "display_order",
    )

    list_filter = (
        "application_type",
        "field_type",
        "is_required",
    )

    search_fields = (
        "label",
        "field_name",
    )

    ordering = (
        "application_type",
        "display_order",
    )


# =========================================================
# APPLICATION FIELD OPTION
# =========================================================

@admin.register(ApplicationFieldOption)
class ApplicationFieldOptionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "field",
        "label",
        "value",
    )

    search_fields = (
        "label",
        "value",
    )

    list_filter = (
        "field",
    )


# =========================================================
# WORKFLOW
# =========================================================

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "application_type",
        "workflow_name",
        "is_active",
        "created_at",
    )

    list_filter = (
        "application_type",
        "is_active",
    )

    search_fields = (
        "workflow_name",
        "description",
    )


# =========================================================
# WORKFLOW STEP
# =========================================================

@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "workflow",
        "step_order",
        "step_name",
        "office",
        "can_approve",
        "can_reject",
        "can_request_revision",
    )

    list_filter = (
        "workflow",
        "office",
        "can_approve",
        "can_reject",
        "can_request_revision",
    )

    search_fields = (
        "step_name",
    )

    ordering = (
        "workflow",
        "step_order",
    )


# =========================================================
# APPLICATION
# =========================================================

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "tracking_number",
        "application_type",
        "student",
        "status",
        "priority",
        "current_step",
        "submitted_at",
    )

    list_filter = (
        "status",
        "priority",
        "application_type",
        "workflow",
    )

    search_fields = (
        "tracking_number",
        "title",
        "student__registration_number",
        "student__user__username",
    )

    readonly_fields = (
        "tracking_number",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )


# =========================================================
# ATTACHMENT
# =========================================================

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "application",
        "file_name",
        "uploaded_by",
        "uploaded_at",
    )

    search_fields = (
        "file_name",
        "application__tracking_number",
        "uploaded_by__username",
    )

    list_filter = (
        "uploaded_at",
    )


# =========================================================
# COMMENT
# =========================================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "application",
        "user",
        "created_at",
    )

    search_fields = (
        "comment",
        "application__tracking_number",
        "user__username",
    )

    list_filter = (
        "created_at",
    )


# =========================================================
# APPROVAL LOG
# =========================================================

@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "application",
        "workflow_step",
        "action_by",
        "action",
        "action_date",
    )

    list_filter = (
        "action",
        "workflow_step",
        "action_date",
    )

    search_fields = (
        "application__tracking_number",
        "action_by__username",
        "remarks",
    )

    readonly_fields = (
        "action_date",
    )