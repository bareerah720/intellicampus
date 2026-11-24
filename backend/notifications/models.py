from django.db import models
from django.conf import settings


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        APPLICATION_SUBMITTED = "application_submitted", "Application Submitted"
        APPLICATION_FORWARDED = "application_forwarded", "Application Forwarded"
        APPLICATION_APPROVED = "application_approved", "Application Approved"
        APPLICATION_REJECTED = "application_rejected", "Application Rejected"
        REVISION_REQUIRED = "revision_required", "Revision Required"
        APPLICATION_RESUBMITTED = "application_resubmitted", "Application Resubmitted"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices
    )

    related_application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="notifications",
        blank=True,
        null=True
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
