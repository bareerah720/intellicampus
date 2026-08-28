from django.urls import path

from .views import (
    ApplicationTypeListCreateView,
    ApplicationTypeDetailView,
    ApplicationActionView,

    ApplicationFieldListCreateView,
    ApplicationFieldDetailView,

    ApplicationFieldOptionListCreateView,
    ApplicationFieldOptionDetailView,

    WorkflowListCreateView,
    WorkflowDetailView,

    WorkflowStepListCreateView,
    WorkflowStepDetailView,

    ApplicationListCreateView,
    ApplicationDetailView,

    AttachmentListCreateView,
    AttachmentDetailView,

    CommentListCreateView,
    CommentDetailView,

    ApprovalLogListCreateView,
    ApprovalLogDetailView,
)


urlpatterns = [

    # =====================================================
    # APPLICATION TYPES
    # =====================================================

    path(
        "types/",
        ApplicationTypeListCreateView.as_view(),
        name="application-type-list-create",
    ),

    path(
        "types/<int:pk>/",
        ApplicationTypeDetailView.as_view(),
        name="application-type-detail",
    ),

    path(
    "<int:pk>/action/",
    ApplicationActionView.as_view(),
    name="application-action",
    ),


    # =====================================================
    # APPLICATION FIELDS
    # =====================================================

    path(
        "fields/",
        ApplicationFieldListCreateView.as_view(),
        name="application-field-list-create",
    ),

    path(
        "fields/<int:pk>/",
        ApplicationFieldDetailView.as_view(),
        name="application-field-detail",
    ),


    # =====================================================
    # FIELD OPTIONS
    # =====================================================

    path(
        "field-options/",
        ApplicationFieldOptionListCreateView.as_view(),
        name="application-field-option-list-create",
    ),

    path(
        "field-options/<int:pk>/",
        ApplicationFieldOptionDetailView.as_view(),
        name="application-field-option-detail",
    ),


    # =====================================================
    # WORKFLOWS
    # =====================================================

    path(
        "workflows/",
        WorkflowListCreateView.as_view(),
        name="workflow-list-create",
    ),

    path(
        "workflows/<int:pk>/",
        WorkflowDetailView.as_view(),
        name="workflow-detail",
    ),


    # =====================================================
    # WORKFLOW STEPS
    # =====================================================

    path(
        "workflow-steps/",
        WorkflowStepListCreateView.as_view(),
        name="workflow-step-list-create",
    ),

    path(
        "workflow-steps/<int:pk>/",
        WorkflowStepDetailView.as_view(),
        name="workflow-step-detail",
    ),


    # =====================================================
    # APPLICATIONS
    # =====================================================

    path(
        "",
        ApplicationListCreateView.as_view(),
        name="application-list-create",
    ),

    path(
        "<int:pk>/",
        ApplicationDetailView.as_view(),
        name="application-detail",
    ),


    # =====================================================
    # ATTACHMENTS
    # =====================================================

    path(
        "attachments/",
        AttachmentListCreateView.as_view(),
        name="attachment-list-create",
    ),

    path(
        "attachments/<int:pk>/",
        AttachmentDetailView.as_view(),
        name="attachment-detail",
    ),


    # =====================================================
    # COMMENTS
    # =====================================================

    path(
        "comments/",
        CommentListCreateView.as_view(),
        name="comment-list-create",
    ),

    path(
        "comments/<int:pk>/",
        CommentDetailView.as_view(),
        name="comment-detail",
    ),


    # =====================================================
    # APPROVAL LOGS
    # =====================================================

    path(
        "approval-logs/",
        ApprovalLogListCreateView.as_view(),
        name="approval-log-list-create",
    ),

    path(
        "approval-logs/<int:pk>/",
        ApprovalLogDetailView.as_view(),
        name="approval-log-detail",
    ),
]