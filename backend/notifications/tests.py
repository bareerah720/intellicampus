from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.db.models import Q
from django.test import SimpleTestCase

from applications.models import ApplicationStatus
from notifications.services import notify_current_officers


def _value_for(obj, expression):
    parts = expression.split("__")
    lookup = parts[-1] if parts[-1] in {"lte", "gte", "isnull"} else "exact"
    if lookup != "exact":
        parts.pop()
    value = obj
    for part in parts:
        if value is None:
            return None, lookup
        value = getattr(value, part)
    return value, lookup


def _matches_q(obj, query):
    def evaluate(child):
        if isinstance(child, Q):
            return _matches_q(obj, child)
        expression, expected = child
        value, lookup = _value_for(obj, expression)
        if value is None and lookup in {"lte", "gte"}:
            return False
        return {
            "exact": lambda: value == expected,
            "lte": lambda: value <= expected,
            "gte": lambda: value >= expected,
            "isnull": lambda: (value is None) == expected,
        }[lookup]()

    outcomes = (evaluate(child) for child in query.children)
    result = all(outcomes) if query.connector == Q.AND else any(outcomes)
    return not result if query.negated else result


class _AssignmentQuerySet:
    """Small in-memory queryset double; tests do not need a database."""

    def __init__(self, rows):
        self.rows = rows

    def filter(self, *conditions, **criteria):
        def matches(row):
            for expression, expected in criteria.items():
                value, lookup = _value_for(row, expression)
                if value is None and lookup in {"lte", "gte"}:
                    return False
                valid = {
                    "exact": lambda: value == expected,
                    "lte": lambda: value <= expected,
                    "gte": lambda: value >= expected,
                    "isnull": lambda: (value is None) == expected,
                }[lookup]()
                if not valid:
                    return False
            return all(_matches_q(row, condition) for condition in conditions)

        return _AssignmentQuerySet([row for row in self.rows if matches(row)])

    def select_related(self, *args):
        return self

    def __iter__(self):
        return iter(self.rows)


class NotifyCurrentOfficersTests(SimpleTestCase):
    def setUp(self):
        self.today = date(2026, 11, 23)
        self.application = SimpleNamespace(
            current_step_id=12,
            status=ApplicationStatus.SUBMITTED,
            current_step=SimpleNamespace(
                office_id=7,
                required_responsibility=None,
            ),
            student=SimpleNamespace(
                program=SimpleNamespace(department_id=3),
                batch_id=20,
            ),
        )

    def assignment(
        self,
        user_id,
        responsibility,
        *,
        person_type="faculty",
        department_id=None,
        batch_id=None,
        office_id=7,
        active=True,
        start_date=None,
        end_date=None,
    ):
        user = SimpleNamespace(
            id=user_id,
            is_active=active,
            user_type=person_type,
        )
        return SimpleNamespace(
            is_active=active,
            start_date=start_date or date(2020, 1, 1),
            end_date=end_date,
            office_id=office_id,
            responsibility_type=responsibility,
            department_id=department_id,
            batch_id=batch_id,
            faculty_id=user_id if person_type == "faculty" else None,
            staff_id=user_id if person_type == "staff" else None,
            faculty=SimpleNamespace(user=user) if person_type == "faculty" else None,
            staff=SimpleNamespace(user=user) if person_type == "staff" else None,
        )

    def notify_with(self, assignments):
        queryset = _AssignmentQuerySet(assignments)
        with (
            patch("notifications.services.timezone.localdate", return_value=self.today),
            patch(
                "notifications.services.ResponsibilityAssignment.objects.filter",
                side_effect=lambda *conditions, **criteria: queryset.filter(
                    *conditions,
                    **criteria,
                ),
            ),
            patch("notifications.services.Notification.objects.create") as create,
        ):
            notify_current_officers(
                self.application,
                "Waiting for review",
                "An application is ready for review.",
                "application_submitted",
            )
        return [call.kwargs["recipient"] for call in create.call_args_list]

    def test_unrestricted_step_notifies_only_scoped_eligible_officers_once(self):
        self.application.current_step.required_responsibility = ""
        assignments = [
            self.assignment(1, "hod", department_id=3),
            self.assignment(1, "finance_officer"),  # Same person, deduplicated.
            self.assignment(2, "advisor", person_type="staff", batch_id=20),
            self.assignment(3, "hod", department_id=99),
            self.assignment(4, "advisor", batch_id=21),
            self.assignment(5, "advisor"),  # Advisor needs a batch scope.
            self.assignment(6, "hod", department_id=3, office_id=8),
            self.assignment(7, "hod", department_id=3, active=False),
            self.assignment(8, "hod", department_id=3, end_date=date(2026, 11, 22)),
        ]

        recipients = self.notify_with(assignments)

        self.assertEqual({user.id for user in recipients}, {1, 2})
        self.assertEqual(len(recipients), 2)

    def test_specific_responsibility_excludes_other_assignment_types(self):
        self.application.current_step.required_responsibility = "advisor"
        assignments = [
            self.assignment(1, "advisor", batch_id=20),
            self.assignment(2, "advisor", batch_id=21),
            self.assignment(3, "hod", department_id=3),
        ]

        recipients = self.notify_with(assignments)

        self.assertEqual([user.id for user in recipients], [1])
