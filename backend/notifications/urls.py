
from django.urls import path

from .views import (
    NotificationListView,
    UnreadNotificationCountView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
)

urlpatterns = [
    path(
        "",
        NotificationListView.as_view(),
        name="notification-list"
    ),

    path(
        "unread-count/",
        UnreadNotificationCountView.as_view(),
        name="unread-notification-count"
    ),

    path(
        "mark-all-read/",
        MarkAllNotificationsReadView.as_view(),
        name="mark-all-notifications-read"
    ),

    path(
        "<int:pk>/mark-read/",
        MarkNotificationReadView.as_view(),
        name="mark-notification-read"
    ),
]
