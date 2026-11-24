import os
from datetime import date
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from accounts.models import User
from accounts.management.commands.reset_and_seed_demo import (
    BATCH_SPECS,
    OLD_OFFICE_TO_NEW_CODE,
    Command,
    semester_number_at,
)


class ResetAndSeedDemoCommandTests(SimpleTestCase):
    def setUp(self):
        self.default_password = "Temporary Demo Password 2026"
        password_env = patch.dict(
            os.environ,
            {"DEMO_DEFAULT_PASSWORD": self.default_password},
        )
        password_env.start()
        self.addCleanup(password_env.stop)

    @patch.object(Command, "_execute_reset")
    @patch.object(Command, "_preflight", return_value={
        "users_to_replace": 0,
        "applications": 0,
        "notifications": 0,
        "responsibility_assignments": 0,
        "application_types": 0,
        "dynamic_fields": 0,
        "field_options": 0,
        "workflows": 0,
        "workflow_steps": 0,
        "old_office_codes": [],
    })
    def test_default_invocation_is_dry_run(self, preflight, execute_reset):
        output = StringIO()
        call_command("reset_and_seed_demo", stdout=output)
        preflight.assert_called_once_with()
        execute_reset.assert_not_called()
        self.assertIn("DRY RUN", output.getvalue())
        self.assertNotIn(self.default_password, output.getvalue())

    @patch.object(Command, "_execute_reset")
    @patch.object(Command, "_preflight", return_value={
        "users_to_replace": 0,
        "applications": 0,
        "notifications": 0,
        "responsibility_assignments": 0,
        "application_types": 0,
        "dynamic_fields": 0,
        "field_options": 0,
        "workflows": 0,
        "workflow_steps": 0,
        "old_office_codes": [],
    })
    def test_execute_flag_is_the_only_path_to_reset(self, preflight, execute_reset):
        call_command("reset_and_seed_demo", execute=True, stdout=StringIO())
        execute_reset.assert_called_once_with()

    @patch.object(Command, "_execute_reset")
    @patch.object(Command, "_preflight", side_effect=CommandError("preflight failed"))
    def test_preflight_failure_prevents_execution(self, preflight, execute_reset):
        with self.assertRaises(CommandError):
            call_command("reset_and_seed_demo", execute=True, stdout=StringIO())
        execute_reset.assert_not_called()

    def test_missing_or_empty_password_fails_before_preflight_or_reset(self):
        for configured_value in (None, ""):
            with self.subTest(configured_value="missing" if configured_value is None else "empty"):
                with patch.dict(os.environ):
                    if configured_value is None:
                        os.environ.pop("DEMO_DEFAULT_PASSWORD", None)
                    else:
                        os.environ["DEMO_DEFAULT_PASSWORD"] = configured_value
                    with (
                        patch.object(Command, "_preflight") as preflight,
                        patch.object(Command, "_execute_reset") as execute_reset,
                    ):
                        with self.assertRaisesRegex(
                            CommandError,
                            "DEMO_DEFAULT_PASSWORD",
                        ):
                            call_command("reset_and_seed_demo", execute=True, stdout=StringIO())
                    preflight.assert_not_called()
                    execute_reset.assert_not_called()

    def test_all_demo_roles_receive_the_same_environment_password(self):
        command = Command()
        command._demo_default_password = command._configured_demo_password()
        created_users = []
        with patch.object(User, "save"):
            for user_type in ("student", "faculty", "staff"):
                created_users.append(command._create_user(
                    slug=f"{user_type}.test",
                    first_name="Demo",
                    last_name="User",
                    user_type=user_type,
                ))
        for user in created_users:
            self.assertTrue(user.check_password(self.default_password))
            self.assertNotEqual(user.password, self.default_password)
            self.assertTrue(user.must_change_password)

    def test_student_distribution_is_exactly_100_and_balanced(self):
        counts = [students for _, _, _, students in BATCH_SPECS]
        self.assertEqual(sum(counts), 100)
        self.assertEqual(sorted(counts), [12, 12, 12, 12, 13, 13, 13, 13])
        for program_code in ("CS", "SE", "CE", "EE"):
            self.assertEqual(
                sum(count for _, code, _, count in BATCH_SPECS if code == program_code),
                25,
            )

    def test_semester_calculation_counts_admission_term_and_caps_at_program_length(self):
        spring_2023 = SimpleNamespace(
            session_type="spring", start_date=date(2023, 2, 1)
        )
        fall_2023 = SimpleNamespace(
            session_type="fall", start_date=date(2023, 9, 1)
        )
        fall_2026 = SimpleNamespace(
            session_type="fall", start_date=date(2026, 9, 1)
        )
        self.assertEqual(semester_number_at(fall_2026, spring_2023, 8), 8)
        self.assertEqual(semester_number_at(fall_2026, fall_2023, 8), 7)
        self.assertEqual(semester_number_at(fall_2026, fall_2023, 4), 4)

    def test_old_office_map_covers_all_preserved_routing_codes(self):
        self.assertEqual(len(OLD_OFFICE_TO_NEW_CODE), 5)
        self.assertIn("CS-OFFICE", OLD_OFFICE_TO_NEW_CODE)
        self.assertIn("FEE-OFFICE", OLD_OFFICE_TO_NEW_CODE)
        self.assertIn("SCHOLAR", OLD_OFFICE_TO_NEW_CODE)
        self.assertIn("ADMIN-OFFICE", OLD_OFFICE_TO_NEW_CODE)
        self.assertIn("EXAM-OFFICE", OLD_OFFICE_TO_NEW_CODE)
