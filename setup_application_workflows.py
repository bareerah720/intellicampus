
from django.db import transaction
from accounts.models import Office
from applications.models import ApplicationType, Workflow, WorkflowStep

# Get all offices
offices = {
    "CS": Office.objects.get(code="CS-OFFICE"),
    "Fee": Office.objects.get(code="FEE-OFFICE"),
    "Scholarship": Office.objects.get(code="SCHOLAR"),
    "Admin": Office.objects.get(code="ADMIN-OFFICE"),
    "Examination": Office.objects.get(code="EXAM-OFFICE"),
}

# Application type ID -> correct office
application_offices = {
    1: "CS",
    2: "CS",
    4: "Fee",
    3: "Scholarship",
    5: "Admin",
    7: "Admin",
    6: "Examination",
}

# Workflow ID -> step configurations
workflow_steps = {
    1: [
        (1, "Batch Advisor Approval", "advisor", "CS"),
        (2, "HOD Approval", "hod", "CS"),
    ],
    6: [
        (1, "Student Submission", None, "CS"),
        (2, "Advisor Review", "advisor", "CS"),
        (3, "HOD Review", "hod", "CS"),
    ],
    2: [
        (1, "Student Submission", None, "Fee"),
        (2, "Advisor Review", "advisor", "CS"),
        (3, "HOD Review", "hod", "CS"),
        (4, "Finance Officer Review", "finance_officer", "Fee"),
    ],
    7: [
        (1, "Student Submission", None, "Scholarship"),
        (2, "Advisor Review", "advisor", "CS"),
        (3, "HOD Review", "hod", "CS"),
        (4, "Scholarship Coordinator Review", "scholarship_coordinator", "Scholarship"),
    ],
    3: [
        (1, "Student Submission", None, "Admin"),
        (2, "Student Affairs Officer Review", "student_affairs_officer", "Admin"),
    ],
    5: [
        (1, "Student Submission", None, "Admin"),
        (2, "Student Affairs Officer Review", "student_affairs_officer", "Admin"),
    ],
    4: [
        (1, "Student Submission", None, "Examination"),
        (2, "Exam Officer Review", "exam_officer", "Examination"),
    ],
}

with transaction.atomic():

    # 1. Update application type offices
    for type_id, office_key in application_offices.items():
        application_type = ApplicationType.objects.get(pk=type_id)
        application_type.office = offices[office_key]
        application_type.save(update_fields=["office"])
        print("Application type updated:", application_type.name, office_key)

    # 2. Configure workflow steps
    for workflow_id, steps in workflow_steps.items():
        workflow = Workflow.objects.get(pk=workflow_id)

        for order, name, responsibility, office_key in steps:

            step, created = WorkflowStep.objects.get_or_create(
                workflow=workflow,
                step_order=order,
                defaults={
                    "step_name": name,
                    "office": offices[office_key],
                    "required_responsibility": responsibility,
                }
            )

            if not created:
                step.step_name = name
                step.office = offices[office_key]
                step.required_responsibility = responsibility
                step.save()

            print(
                "Step configured:",
                workflow.workflow_name,
                "|",
                name,
                "|",
                responsibility,
                "|",
                office_key
            )

print("All application workflows configured successfully!")
