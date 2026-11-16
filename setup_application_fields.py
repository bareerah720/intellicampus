from applications.models import ApplicationType, ApplicationField, ApplicationFieldOption

FIELD_CONFIG = {
    "Course Drop": [
        ("Course Code", "course_code", "text", True, "Enter course code", []),
        ("Course Name", "course_name", "text", True, "Enter course name", []),
        ("Reason", "reason", "textarea", True, "Explain why you want to drop this course", []),
    ],

    "Course Registration": [
        ("Course Code", "course_code", "text", True, "Enter course code", []),
        ("Course Name", "course_name", "text", True, "Enter course name", []),
        ("Semester", "semester", "dropdown", True, "Select semester", [
            ("Fall", "Fall"),
            ("Spring", "Spring"),
            ("Summer", "Summer"),
        ]),
    ],

    "Fee Installment": [
        ("Total Fee Due", "total_fee_due", "number", True, "Enter total outstanding fee", []),
        ("Number of Installments", "number_of_installments", "dropdown", True, "Select installments", [
            ("2 Installments", "2"),
            ("3 Installments", "3"),
            ("4 Installments", "4"),
        ]),
        ("Reason", "reason", "textarea", True, "Explain your financial situation", []),
    ],

    "Scholarship": [
        ("Scholarship Name", "scholarship_name", "text", True, "Enter scholarship name", []),
        ("Current GPA", "current_gpa", "number", True, "Enter your current GPA", []),
        ("Reason", "reason", "textarea", True, "Explain why you are applying", []),
    ],

    "Bonafide Certificate": [
        ("Required For", "required_for", "dropdown", True, "Select purpose", [
            ("Higher Studies", "higher_studies"),
            ("Job Application", "job_application"),
            ("Bank", "bank"),
            ("Other", "other"),
        ]),
        ("Details", "details", "textarea", True, "Provide additional details", []),
    ],

    "Degree Application": [
        ("Completion Semester", "completion_semester", "dropdown", True, "Select semester", [
            ("Fall", "Fall"),
            ("Spring", "Spring"),
            ("Summer", "Summer"),
        ]),
        ("Completion Year", "completion_year", "number", True, "Enter completion year", []),
        ("Additional Details", "additional_details", "textarea", False, "Enter additional details", []),
    ],

    "Transcript": [
        ("Transcript Purpose", "transcript_purpose", "dropdown", True, "Select purpose", [
            ("Higher Studies", "higher_studies"),
            ("Job Application", "job_application"),
            ("Personal Record", "personal_record"),
            ("Other", "other"),
        ]),
        ("Number of Copies", "number_of_copies", "number", True, "Enter number of copies", []),
        ("Collection Method", "collection_method", "dropdown", True, "Select collection method", [
            ("Collect from Office", "office_collection"),
            ("Courier", "courier"),
        ]),
    ],
}

for type_name, fields in FIELD_CONFIG.items():
    application_type = ApplicationType.objects.get(name=type_name)

    for order, config in enumerate(fields, start=1):
        label, field_name, field_type, required, placeholder, options = config

        field, created = ApplicationField.objects.update_or_create(
            application_type=application_type,
            field_name=field_name,
            defaults={
                "label": label,
                "field_type": field_type,
                "is_required": required,
                "placeholder": placeholder,
                "display_order": order,
            },
        )

        for option_label, option_value in options:
            ApplicationFieldOption.objects.update_or_create(
                field=field,
                value=option_value,
                defaults={"label": option_label},
            )

    print(f"Configured: {type_name}")

print("\nApplication fields setup completed successfully.")
print("Total fields:", ApplicationField.objects.count())
print("Total dropdown options:", ApplicationFieldOption.objects.count())
