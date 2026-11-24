# Repository guidance

## Project architecture

- The backend is Django and Django REST Framework.
- Accounts, roles, profiles, academic sessions, batches, and responsibility
  assignments are implemented under `backend/accounts`.
- Applications and their approval workflows are implemented under
  `backend/applications`; notification routing is under
  `backend/notifications`.
- The frontend is React under `frontend/src`.
- The project uses a custom Django `User` model and JWT authentication.
  Preserve the configured user model and authentication flow.

## Roles and permissions

- Existing account types are student, faculty, staff, admin, and external
  examiner. Do not add a new account role without explicit approval.
- Central Admin is provisioned through a controlled process, not normal User
  Management. Do not create another Central Admin through ordinary user APIs.
- Preserve existing JWT behavior and role permission checks.
- Staff and faculty do not receive academic-hold approval rights by account
  type alone. Approval requires an appropriate active ResponsibilityAssignment.
- HOD responsibility is department-scoped. The `academic_hold_approver`
  responsibility is only for explicitly delegated authority.
- Keep hold decisions auditable and prevent a requester from approving their
  own request.

## Academic-session rules

- The university has one current academic session at a time.
- Spring runs February 1 through July 31.
- Fall runs September 1 through January 31 of the following year.
- August is a break and is not an academic session.
- A student's admission session is permanent and determines the student's
  cohort, batch name, and registration-number prefix.
- The admission session counts as Semester 1. Each subsequent Spring or Fall
  session advances progression by one, subject to the program's effective
  semester count.
- The shared Semester catalog contains ordinals 1 through 8. A program may use
  only ordinals up to its effective semester count.
- Default effective semester count is `duration_years * 2`. A different
  `total_semesters` is allowed only as an explicitly approved program exception.
- An approved academic hold overlapping a session pauses that entire session.
  Count each paused session once per student, even if multiple approved holds
  overlap it. Pending and rejected holds do not pause progression.
- Stop progression at the program's final semester. Do not infer a student's
  current semester from graduation year alone.

## Data and database safety

- Do not assume existing database records are valid university policy; they may
  be dummy data.
- Never reset, delete, bulk-rewrite, or seed database records without explicit
  approval of the exact environment and operation.
- Treat schema migrations and dummy-data reset as separate operations. Never
  embed a reset in a migration.
- Before proposing or running a migration, inspect database configuration,
  migration state, constraints, dependent records, and backup/rollback options.
- Do not run migrations or destructive database commands without explicit
  authorization.
- Preserve application history, student login identifiers, batch-based
  responsibility assignments, and foreign-key relationships unless a reviewed
  migration plan explicitly addresses them.

## Before modifying code

- Read this file and inspect the relevant existing models, serializers, views,
  permissions, URLs, admin registrations, frontend service calls, and all
  references to affected fields.
- Follow existing API and routing conventions. Identify all consumers before
  changing a response field or request contract.
- Keep generated academic values server-controlled and validate them at the
  API and model/database layers as appropriate.
- Do not delete backup files or treat backups as active implementation.
- Summarize intended changes and risks before broad or cross-application edits.
- Run only validation commands relevant to the requested change and report
  their results accurately.
