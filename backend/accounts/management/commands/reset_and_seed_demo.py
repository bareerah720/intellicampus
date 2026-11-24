"""Safely reset demo data while retaining application configuration.

The command is intentionally read-only unless invoked with ``--execute``.
"""

import os
from datetime import date

from django.core.management import BaseCommand, CommandError
from django.db.migrations.loader import MigrationLoader
from django.db import connection, transaction
from django.db.models import Count
from django.utils import timezone

from accounts.models import (
    AcademicSession,
    Batch,
    Department,
    FacultyProfile,
    Office,
    Program,
    ResponsibilityAssignment,
    Semester,
    StaffProfile,
    StudentProfile,
    User,
    UserType,
)
from applications.models import (
    Application,
    ApplicationField,
    ApplicationFieldOption,
    ApplicationType,
    Attachment,
    ApprovalLog,
    Comment,
    Workflow,
    WorkflowStep,
)
from notifications.models import Notification


OLD_OFFICE_TO_NEW_CODE = {
    "CS-OFFICE": "ACAD-AFFAIRS",
    "FEE-OFFICE": "FINANCE-OPS",
    "SCHOLAR": "SCHOLARSHIP-OPS",
    "ADMIN-OFFICE": "STUDENT-AFFAIRS",
    "EXAM-OFFICE": "EXAM-OPS",
}

OFFICE_SPECS = (
    ("Academic Affairs Office", "ACAD-AFFAIRS"),
    ("Finance Operations Office", "FINANCE-OPS"),
    ("Scholarship Services Office", "SCHOLARSHIP-OPS"),
    ("Student Affairs Office", "STUDENT-AFFAIRS"),
    ("Examination Services Office", "EXAM-OPS"),
)

DEPARTMENT_SPECS = (
    ("Computer Science Department", "CS"),
    ("Electrical Department", "EE"),
)

PROGRAM_SPECS = (
    ("Computer Science", "CS", "CS"),
    ("Software Engineering", "SE", "CS"),
    ("Computer Engineering", "CE", "EE"),
    ("Electrical Engineering", "EE", "EE"),
)

SESSION_SPECS = (
    ("Spring 2023", "spring", date(2023, 2, 1), date(2023, 7, 31)),
    ("Fall 2023", "fall", date(2023, 9, 1), date(2024, 1, 31)),
    ("Spring 2026", "spring", date(2026, 2, 1), date(2026, 7, 31)),
    ("Fall 2026", "fall", date(2026, 9, 1), date(2027, 1, 31)),
)

BATCH_SPECS = (
    ("CS-Spring23", "CS", "Spring 2023", 13),
    ("CS-Fall23", "CS", "Fall 2023", 12),
    ("SE-Spring23", "SE", "Spring 2023", 13),
    ("SE-Fall23", "SE", "Fall 2023", 12),
    ("CE-Spring26", "CE", "Spring 2026", 13),
    ("CE-Fall26", "CE", "Fall 2026", 12),
    ("EE-Spring26", "EE", "Spring 2026", 13),
    ("EE-Fall26", "EE", "Fall 2026", 12),
)

FACULTY_SPECS = (
    ("hod_cs", "Demo", "HOD CS", "hod.cs", "CS", "Head of Department"),
    ("hod_ee", "Demo", "HOD EE", "hod.ee", "EE", "Head of Department"),
    ("advisor_cs_1", "Demo", "Advisor CS 1", "advisor.cs.1", "CS", "Advisor"),
    ("advisor_cs_2", "Demo", "Advisor CS 2", "advisor.cs.2", "CS", "Advisor"),
    ("advisor_ee_1", "Demo", "Advisor EE 1", "advisor.ee.1", "EE", "Advisor"),
    ("advisor_ee_2", "Demo", "Advisor EE 2", "advisor.ee.2", "EE", "Advisor"),
    ("lecturer_cs", "Demo", "Lecturer CS", "lecturer.cs", "CS", "Lecturer"),
    ("lecturer_ee", "Demo", "Lecturer EE", "lecturer.ee", "EE", "Lecturer"),
)

STAFF_SPECS = (
    ("finance_staff", "Demo", "Finance Officer", "finance.officer", "FINANCE-OPS", "Finance Officer", "finance_officer"),
    ("scholarship_staff", "Demo", "Scholarship Officer", "scholarship.officer", "SCHOLARSHIP-OPS", "Scholarship Coordinator", "scholarship_coordinator"),
    ("student_affairs_staff", "Demo", "Student Affairs Officer", "student.affairs", "STUDENT-AFFAIRS", "Student Affairs Officer", "student_affairs_officer"),
    ("exam_staff", "Demo", "Examination Officer", "exam.officer", "EXAM-OPS", "Examination Officer", "exam_officer"),
)

RESPONSIBILITY_ASSIGNMENT_SPECS = (
    ("advisor_cs_1", "advisor", "CS", ("CS-Spring23", "CS-Fall23")),
    ("advisor_cs_2", "advisor", "CS", ("SE-Spring23", "SE-Fall23")),
    ("advisor_ee_1", "advisor", "EE", ("CE-Spring26", "CE-Fall26")),
    ("advisor_ee_2", "advisor", "EE", ("EE-Spring26", "EE-Fall26")),
)

STUDENT_EMAIL_DOMAIN = "demo.intellicampus.test"
EXPECTED_SEMESTER_NUMBERS = tuple(range(1, 9))


def semester_number_at(current_session, admission_session, semester_count):
    """Return the admission term as 1, counting Spring and Fall only."""
    term_number = {"spring": 0, "fall": 1}
    try:
        admission_index = (
            admission_session.start_date.year * 2
            + term_number[admission_session.session_type]
        )
        current_index = (
            current_session.start_date.year * 2
            + term_number[current_session.session_type]
        )
    except (AttributeError, KeyError) as exc:
        raise ValueError("Only valid Spring and Fall sessions are supported.") from exc

    elapsed_terms = current_index - admission_index + 1
    if elapsed_terms < 1:
        raise ValueError("Admission session cannot be after the current session.")
    return min(elapsed_terms, semester_count)


class Command(BaseCommand):
    help = (
        "Preview the IntelliCampus demo-data reset. Database changes require "
        "the explicit --execute flag."
    )

    reset_models = (
        User,
        StudentProfile,
        FacultyProfile,
        StaffProfile,
        Department,
        Program,
        AcademicSession,
        Batch,
        Office,
        ResponsibilityAssignment,
        Semester,
        ApplicationType,
        ApplicationField,
        ApplicationFieldOption,
        Workflow,
        WorkflowStep,
        Application,
        Attachment,
        Comment,
        ApprovalLog,
        Notification,
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Apply the destructive reset and seed inside one transaction.",
        )

    def handle(self, *args, **options):
        self._demo_default_password = self._configured_demo_password()
        preflight = self._preflight()
        self._print_plan(preflight)

        if not options["execute"]:
            self.stdout.write(self.style.WARNING(
                "DRY RUN: no database changes were made. "
                "Pass --execute to run this reset."
            ))
            return

        self._execute_reset()
        self.stdout.write(self.style.SUCCESS(
            "Demo dataset reset completed: 100 students, 8 faculty, 4 staff."
        ))

    @staticmethod
    def _configured_demo_password():
        password = os.environ.get("DEMO_DEFAULT_PASSWORD")
        if password is None or password == "":
            raise CommandError(
                "Set DEMO_DEFAULT_PASSWORD to a non-empty temporary password "
                "before running reset_and_seed_demo."
            )
        return password

    def _preflight(self):
        if connection.vendor != "postgresql":
            raise CommandError("This reset command is restricted to PostgreSQL.")

        admin = User._base_manager.filter(pk=1, user_type=UserType.ADMIN).first()
        admin_ids = list(
            User._base_manager.filter(user_type=UserType.ADMIN)
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        if admin is None or admin_ids != [1]:
            raise CommandError(
                "Expected exactly one Central Admin with User ID 1; refusing reset."
            )
        if any((
            StudentProfile.objects.filter(user_id=1).exists(),
            FacultyProfile.objects.filter(user_id=1).exists(),
            StaffProfile.objects.filter(user_id=1).exists(),
        )):
            raise CommandError(
                "Central Admin ID 1 has a role profile; refusing to replace catalogs."
            )

        loader = MigrationLoader(connection)
        missing_migrations = [
            ".".join(node)
            for app_label in ("accounts", "applications", "notifications")
            for node in loader.graph.leaf_nodes(app_label)
            if node not in loader.applied_migrations
        ]
        if missing_migrations:
            raise CommandError(
                "Required app migrations are unapplied: "
                + ", ".join(sorted(missing_migrations))
            )

        semester_numbers = tuple(
            Semester.objects.order_by("number").values_list("number", flat=True)
        )
        if semester_numbers != EXPECTED_SEMESTER_NUMBERS:
            raise CommandError(
                "The existing Semester catalog must contain exactly ordinals 1–8."
            )

        old_office_codes = set(Office.objects.values_list("code", flat=True))
        referenced_codes = set(
            ApplicationType.objects.values_list("office__code", flat=True)
        ) | set(WorkflowStep.objects.values_list("office__code", flat=True))
        target_codes = {code for _, code in OFFICE_SPECS}
        known_codes = set(OLD_OFFICE_TO_NEW_CODE) | target_codes
        unknown_codes = referenced_codes - known_codes
        if unknown_codes:
            raise CommandError(
                "Workflow configuration references unmapped office codes: "
                + ", ".join(sorted(unknown_codes))
            )
        missing_codes = set(OLD_OFFICE_TO_NEW_CODE) - old_office_codes
        missing_references = missing_codes & referenced_codes
        if missing_references:
            raise CommandError(
                "Referenced old offices are missing: "
                + ", ".join(sorted(missing_references))
            )

        for name, code in OFFICE_SPECS:
            office_with_code = Office.objects.filter(code=code).first()
            office_with_name = Office.objects.filter(name=name).first()
            if office_with_code and office_with_code.name != name:
                raise CommandError(
                    f"Office code {code} is already assigned to another office."
                )
            if office_with_name and office_with_name.code != code:
                raise CommandError(
                    f"Office name {name} is already assigned to another code."
                )

        return {
            "users_to_replace": User._base_manager.exclude(pk=1).count(),
            "applications": Application.objects.count(),
            "notifications": Notification.objects.count(),
            "responsibility_assignments": ResponsibilityAssignment.objects.count(),
            "application_types": ApplicationType.objects.count(),
            "dynamic_fields": ApplicationField.objects.count(),
            "field_options": ApplicationFieldOption.objects.count(),
            "workflows": Workflow.objects.count(),
            "workflow_steps": WorkflowStep.objects.count(),
            "old_office_codes": sorted(old_office_codes),
        }

    def _print_plan(self, preflight):
        self.stdout.write("IntelliCampus demo reset plan (PostgreSQL)")
        self.stdout.write("Central Admin User ID 1: retained; account fields are verified.")
        self.stdout.write(
            "Will delete: non-admin users/profiles, applications, all notifications, "
            "responsibility assignments and old academic/office catalogs."
        )
        self.stdout.write(
            "Will preserve: Semester catalog, Application Types, Dynamic Fields/options, "
            "Workflows and Workflow Steps; only config office foreign keys are repointed."
        )
        self.stdout.write(
            "Will create: 2 departments, 4 programs, 8 batches, 4 sessions, "
            "5 offices, 8 faculty, 4 staff and exactly 100 students."
        )
        self.stdout.write(
            "Office remap: "
            + ", ".join(
                f"{old}->{new}" for old, new in OLD_OFFICE_TO_NEW_CODE.items()
            )
        )
        self.stdout.write(
            "Students per batch: "
            + ", ".join(f"{name}={count}" for name, _, _, count in BATCH_SPECS)
        )
        self.stdout.write(
            "Current counts: users={users_to_replace} non-admin; applications={applications}; "
            "notifications={notifications}; assignments={responsibility_assignments}; "
            "preserved types={application_types}, fields={dynamic_fields}, "
            "options={field_options}, workflows={workflows}, steps={workflow_steps}.".format(
                **preflight
            )
        )

    def _lock_reset_tables(self):
        models_to_lock = list(self.reset_models)
        models_to_lock.append(User._meta.get_field("groups").remote_field.through)
        models_to_lock.append(
            User._meta.get_field("user_permissions").remote_field.through
        )
        table_names = sorted({model._meta.db_table for model in models_to_lock})
        quoted = ", ".join(connection.ops.quote_name(name) for name in table_names)
        with connection.cursor() as cursor:
            cursor.execute(f"LOCK TABLE {quoted} IN EXCLUSIVE MODE")

    @staticmethod
    def _model_snapshot(model, excluded_fields=()):
        excluded_fields = set(excluded_fields)
        fields = [
            field.attname
            for field in model._meta.concrete_fields
            if field.attname not in excluded_fields
        ]
        return list(model.objects.order_by("pk").values(*fields))

    def _configuration_snapshot(self):
        return {
            "types": self._model_snapshot(ApplicationType, {"office_id"}),
            "fields": self._model_snapshot(ApplicationField),
            "options": self._model_snapshot(ApplicationFieldOption),
            "workflows": self._model_snapshot(Workflow),
            "steps": self._model_snapshot(WorkflowStep, {"office_id"}),
        }

    def _admin_snapshot(self):
        admin = User._base_manager.get(pk=1)
        values = User._base_manager.filter(pk=1).values().get()
        return {
            "fields": values,
            "groups": tuple(admin.groups.order_by("pk").values_list("pk", flat=True)),
            "permissions": tuple(
                admin.user_permissions.order_by("pk").values_list("pk", flat=True)
            ),
        }

    def _execute_reset(self):
        # Validate before opening the transaction or taking destructive locks,
        # including if this internal method is called outside handle().
        self._demo_default_password = self._configured_demo_password()
        with transaction.atomic():
            self._lock_reset_tables()
            self._preflight()
            admin_before = self._admin_snapshot()
            config_before = self._configuration_snapshot()
            app_type_offices = dict(
                ApplicationType.objects.order_by("pk").values_list("pk", "office__code")
            )
            step_offices = dict(
                WorkflowStep.objects.order_by("pk").values_list("pk", "office__code")
            )
            old_offices = dict(Office.objects.values_list("code", "pk"))
            attachment_files = self._attachment_files_for_cleanup()

            Notification.objects.all().delete()
            Application.objects.all().delete()
            ResponsibilityAssignment.objects.all().delete()
            User._base_manager.exclude(pk=1).delete()

            Batch.objects.all().delete()
            Program.objects.all().delete()
            AcademicSession.objects.all().delete()

            # Office.department is nullable. Detach old offices so old
            # departments can be replaced while preserved config still points
            # at the old office rows.
            Office.objects.update(department=None)
            Department.objects.all().delete()

            departments = {
                code: Department.objects.create(name=name, code=code, is_active=True)
                for name, code in DEPARTMENT_SPECS
            }
            programs = {
                code: Program.objects.create(
                    name=name,
                    code=code,
                    department=departments[department_code],
                    duration_years=4,
                    semester_count_override=None,
                    semester_exception_approval_reference=None,
                    semester_exception_approval_note=None,
                    is_active=True,
                )
                for name, code, department_code in PROGRAM_SPECS
            }

            sessions = {}
            for title, session_type, start_date, end_date in SESSION_SPECS:
                sessions[title] = AcademicSession.objects.create(
                    title=title,
                    session_type=session_type,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=False,
                )
            fall_2026 = sessions["Fall 2026"]
            fall_2026.is_current = True
            fall_2026.save(update_fields=["is_current"])

            offices = {}
            for name, code in OFFICE_SPECS:
                office, _ = Office.objects.get_or_create(
                    code=code,
                    defaults={"name": name, "is_active": True},
                )
                office.name = name
                office.department = None
                office.office_location = None
                office.email = None
                office.contact_number = None
                office.is_active = True
                office.save(update_fields=[
                    "name",
                    "department",
                    "office_location",
                    "email",
                    "contact_number",
                    "is_active",
                ])
                offices[code] = office

            expected_type_offices = {
                pk: self._target_office_code(old_code)
                for pk, old_code in app_type_offices.items()
            }
            expected_step_offices = {
                pk: self._target_office_code(old_code)
                for pk, old_code in step_offices.items()
            }
            source_office_map = {
                **OLD_OFFICE_TO_NEW_CODE,
                **{code: code for _, code in OFFICE_SPECS},
            }
            for old_code, new_code in source_office_map.items():
                old_id = old_offices.get(old_code)
                if old_id is None:
                    continue
                new_id = offices[new_code].pk
                ApplicationType.objects.filter(office_id=old_id).update(office_id=new_id)
                WorkflowStep.objects.filter(office_id=old_id).update(office_id=new_id)

            replacement_office_ids = {office.pk for office in offices.values()}
            Office.objects.exclude(pk__in=replacement_office_ids).delete()

            batches = {}
            batch_sessions = {}
            batch_counts = {}
            for name, program_code, session_title, student_count in BATCH_SPECS:
                program = programs[program_code]
                session = sessions[session_title]
                admission_year = session.start_date.year
                batches[name] = Batch.objects.create(
                    name=name,
                    program=program,
                    admission_year=admission_year,
                    graduation_year=admission_year + program.duration_years,
                    is_active=True,
                )
                batch_sessions[name] = session
                batch_counts[name] = student_count

            faculty = {}
            for key, first_name, last_name, slug, department_code, designation in FACULTY_SPECS:
                user = self._create_user(
                    slug=slug,
                    first_name=first_name,
                    last_name=last_name,
                    user_type=UserType.FACULTY,
                )
                faculty[key] = FacultyProfile.objects.create(
                    user=user,
                    employee_id=f"FAC-{slug.upper().replace('.', '-')}",
                    department=departments[department_code],
                    designation=designation,
                    office=offices["ACAD-AFFAIRS"],
                )

            staff = {}
            for key, first_name, last_name, slug, office_code, designation, responsibility in STAFF_SPECS:
                user = self._create_user(
                    slug=slug,
                    first_name=first_name,
                    last_name=last_name,
                    user_type=UserType.STAFF,
                )
                staff[key] = (
                    StaffProfile.objects.create(
                        user=user,
                        employee_id=f"STF-{slug.upper().replace('.', '-')}",
                        office=offices[office_code],
                        designation=designation,
                    ),
                    responsibility,
                    office_code,
                )

            assignment_date = timezone.localdate()
            for key, _, _, _, department_code, _ in FACULTY_SPECS[:2]:
                ResponsibilityAssignment.objects.create(
                    faculty=faculty[key],
                    department=departments[department_code],
                    office=offices["ACAD-AFFAIRS"],
                    responsibility_type="hod",
                    start_date=assignment_date,
                    is_active=True,
                )

            for faculty_key, responsibility, department_code, batch_names in RESPONSIBILITY_ASSIGNMENT_SPECS:
                for batch_name in batch_names:
                    ResponsibilityAssignment.objects.create(
                        faculty=faculty[faculty_key],
                        department=departments[department_code],
                        office=offices["ACAD-AFFAIRS"],
                        batch=batches[batch_name],
                        responsibility_type=responsibility,
                        start_date=assignment_date,
                        is_active=True,
                    )

            for profile, responsibility, office_code in staff.values():
                ResponsibilityAssignment.objects.create(
                    staff=profile,
                    office=offices[office_code],
                    responsibility_type=responsibility,
                    start_date=assignment_date,
                    is_active=True,
                )

            semester_by_number = {
                semester.number: semester
                for semester in Semester.objects.all()
            }
            for code, program in programs.items():
                if program.effective_semester_count > len(semester_by_number):
                    raise CommandError(
                        f"Program {code} exceeds the preserved Semester catalog."
                    )

            student_index = 0
            for batch_name, _, session_title, expected_students in BATCH_SPECS:
                program = batches[batch_name].program
                admission_session = batch_sessions[batch_name]
                current_semester_number = semester_number_at(
                    fall_2026,
                    admission_session,
                    program.effective_semester_count,
                )
                if expected_students != batch_counts[batch_name]:
                    raise CommandError("Student allocation changed during reset.")
                for _ in range(expected_students):
                    student_index += 1
                    user = self._create_user(
                        slug=f"student.{student_index:03d}",
                        first_name="Demo",
                        last_name=f"Student{student_index:03d}",
                        user_type=UserType.STUDENT,
                    )
                    # registration_number is intentionally blank so the
                    # existing StudentProfile.save() generator remains the
                    # source of registration identifiers.
                    StudentProfile.objects.create(
                        user=user,
                        registration_number="",
                        program=program,
                        batch=batches[batch_name],
                        current_semester=semester_by_number[current_semester_number],
                        academic_session=admission_session,
                        cgpa=0,
                    )

            if student_index != 100:
                raise CommandError("The demo student allocation must total exactly 100.")

            self._verify_seed(
                expected_type_offices=expected_type_offices,
                expected_step_offices=expected_step_offices,
                config_before=config_before,
                admin_before=admin_before,
            )

            if attachment_files:
                transaction.on_commit(
                    lambda files=attachment_files: self._delete_attachment_files(files),
                    robust=True,
                )

    def _create_user(self, slug, first_name, last_name, user_type):
        email = f"{slug}@{STUDENT_EMAIL_DOMAIN}"
        user = User(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            is_active=True,
            must_change_password=True,
        )
        user.set_password(self._demo_default_password)
        user.save()
        return user

    @staticmethod
    def _target_office_code(code):
        if code in OLD_OFFICE_TO_NEW_CODE:
            return OLD_OFFICE_TO_NEW_CODE[code]
        target_codes = {office_code for _, office_code in OFFICE_SPECS}
        if code in target_codes:
            return code
        raise CommandError(f"No replacement office mapping exists for {code}.")

    @staticmethod
    def _attachment_files_for_cleanup():
        files = []
        for attachment in Attachment.objects.exclude(file_path="").only("file_path"):
            name = attachment.file_path.name
            if name.startswith("application_attachments/"):
                files.append((attachment.file_path.storage, name))
        return tuple(files)

    def _delete_attachment_files(self, files):
        failed = 0
        for storage, name in files:
            try:
                storage.delete(name)
            except Exception:  # noqa: BLE001 - report safely without file paths
                failed += 1
        if failed:
            self.stderr.write(
                self.style.WARNING(
                    f"Database reset committed; {failed} attachment file(s) could not be removed."
                )
            )

    def _verify_seed(
        self,
        expected_type_offices,
        expected_step_offices,
        config_before,
        admin_before,
    ):
        if User._base_manager.filter(pk=1, user_type=UserType.ADMIN).count() != 1:
            raise CommandError("Central Admin ID 1 was not preserved; rolling back.")
        if self._admin_snapshot() != admin_before:
            raise CommandError("Central Admin ID 1 changed; rolling back.")

        if self._configuration_snapshot() != config_before:
            raise CommandError(
                "Preserved application configuration changed beyond office links; rolling back."
            )

        offices = dict(Office.objects.values_list("code", "pk"))
        for model, expected in (
            (ApplicationType, expected_type_offices),
            (WorkflowStep, expected_step_offices),
        ):
            actual = dict(model.objects.order_by("pk").values_list("pk", "office__code"))
            if actual != expected:
                raise CommandError(
                    "Preserved workflow office mappings do not match the reviewed map; rolling back."
                )

        expected_role_counts = {
            UserType.ADMIN: 1,
            UserType.FACULTY: 8,
            UserType.STAFF: 4,
            UserType.STUDENT: 100,
        }
        actual_role_counts = dict(
            User._base_manager.values("user_type")
            .annotate(total=Count("pk"))
            .values_list("user_type", "total")
        )
        if actual_role_counts != expected_role_counts:
            raise CommandError("Final user counts differ from the approved dataset; rolling back.")
        if StudentProfile.objects.count() != 100:
            raise CommandError("Final student profile count is not 100; rolling back.")
        if FacultyProfile.objects.count() != 8 or StaffProfile.objects.count() != 4:
            raise CommandError("Final employee profile counts differ; rolling back.")
        if set(Batch.objects.values_list("name", flat=True)) != {
            name for name, _, _, _ in BATCH_SPECS
        }:
            raise CommandError("Final batch set differs from the approved dataset; rolling back.")
        if set(Department.objects.values_list("code", flat=True)) != {"CS", "EE"}:
            raise CommandError("Final department set differs from the approved dataset; rolling back.")
        if set(Program.objects.values_list("code", flat=True)) != {"CS", "SE", "CE", "EE"}:
            raise CommandError("Final program set differs from the approved dataset; rolling back.")
        expected_session_titles = {item[0] for item in SESSION_SPECS}
        if set(AcademicSession.objects.values_list("title", flat=True)) != expected_session_titles:
            raise CommandError("Final session set differs from the approved dataset; rolling back.")
        if AcademicSession.objects.filter(is_current=True).count() != 1:
            raise CommandError("Exactly one current session is required; rolling back.")
        if not AcademicSession.objects.filter(title="Fall 2026", is_current=True).exists():
            raise CommandError("Fall 2026 must be the only current session; rolling back.")
        if set(offices) != {code for _, code in OFFICE_SPECS}:
            raise CommandError("Final office set differs from the approved dataset; rolling back.")

        expected_assignment_counts = {
            "advisor": 8,
            "hod": 2,
            "finance_officer": 1,
            "scholarship_coordinator": 1,
            "student_affairs_officer": 1,
            "exam_officer": 1,
        }
        actual_assignment_counts = dict(
            ResponsibilityAssignment.objects.values("responsibility_type")
            .annotate(total=Count("pk"))
            .values_list("responsibility_type", "total")
        )
        if actual_assignment_counts != expected_assignment_counts:
            raise CommandError(
                "Responsibility assignments do not cover the preserved workflow; rolling back."
            )

        for batch_name, _, _, expected_students in BATCH_SPECS:
            actual_students = StudentProfile.objects.filter(batch__name=batch_name).count()
            if actual_students != expected_students:
                raise CommandError(
                    "Student distribution differs from the approved allocation; rolling back."
                )

        for program_code in ("CS", "SE", "CE", "EE"):
            actual_students = StudentProfile.objects.filter(
                program__code=program_code
            ).count()
            if actual_students != 25:
                raise CommandError(
                    "Each program must contain 25 students; rolling back."
                )
