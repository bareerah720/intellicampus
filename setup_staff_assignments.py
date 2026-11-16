
from django.utils import timezone
from accounts.models import ResponsibilityAssignment, StaffProfile, Office

today = timezone.localdate()

assignment_data = [
    ("staff01", "finance_officer", "Fee Office"),
    ("staff02", "exam_officer", "Examination Office"),
    ("staff012", "student_affairs_officer", "Admin Office"),
    ("staff012", "scholarship_coordinator", "Scholarship Office"),
]

for username, responsibility, office_name in assignment_data:
    staff = StaffProfile.objects.get(user__username=username)
    office = Office.objects.get(name=office_name)

    assignment, created = ResponsibilityAssignment.objects.get_or_create(
        staff=staff,
        responsibility_type=responsibility,
        office=office,
        is_active=True,
        defaults={"start_date": today}
    )

    print(
        username,
        responsibility,
        office_name,
        "Created" if created else "Already exists"
    )

print("Staff assignments setup completed!")
