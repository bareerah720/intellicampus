from django.db.models import Q
from django.utils import timezone

from accounts.models import ResponsibilityAssignment
from applications.models import ApplicationStatus
from .models import Notification


def create_notification(
    recipient,
    title,
    message,
    notification_type,
    application
):
    if not recipient:
        return None

    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        related_application=application,
    )


def notify_student(
    application,
    title,
    message,
    notification_type
):
    return create_notification(
        recipient=application.student.user,
        title=title,
        message=message,
        notification_type=notification_type,
        application=application,
    )


def notify_current_officers(
    application,
    title,
    message,
    notification_type
):
    if not application.current_step_id:
        return

    if application.status not in (
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.IN_PROGRESS,
    ):
        return

    step = application.current_step

    if not step.office_id:
        return

    today = timezone.localdate()

    assignments = (
        ResponsibilityAssignment.objects
        .filter(
            is_active=True,
            start_date__lte=today,
            office_id=step.office_id,
        )
        .filter(
            Q(end_date__isnull=True) |
            Q(end_date__gte=today)
        )
        .filter(
            Q(
                faculty__user__is_active=True,
                faculty__user__user_type="faculty",
            ) |
            Q(
                staff__user__is_active=True,
                staff__user__user_type="staff",
            )
        )
        .select_related(
            "faculty__user",
            "staff__user",
        )
    )

    if step.required_responsibility:
        assignments = assignments.filter(
            responsibility_type=step.required_responsibility
        )

    notified_users = set()

    for assignment in assignments:

        if (
            assignment.responsibility_type == "advisor"
            and not assignment.batch_id
        ):
            continue

        if (
            assignment.responsibility_type == "hod"
            and not assignment.department_id
        ):
            continue

        if (
            assignment.department_id
            and assignment.department_id
            != application.student.program.department_id
        ):
            continue

        if (
            assignment.batch_id
            and assignment.batch_id
            != application.student.batch_id
        ):
            continue

        officer_user = None

        if assignment.faculty_id:
            officer_user = assignment.faculty.user

        elif assignment.staff_id:
            officer_user = assignment.staff.user

        if not officer_user:
            continue

        if officer_user.id in notified_users:
            continue

        create_notification(
            recipient=officer_user,
            title=title,
            message=message,
            notification_type=notification_type,
            application=application,
        )

        notified_users.add(officer_user.id)
