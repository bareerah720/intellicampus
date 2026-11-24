from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class UserType(models.TextChoices):
    STUDENT = "student", "Student"
    FACULTY = "faculty", "Faculty"
    STAFF = "staff", "Staff"
    ADMIN = "admin", "Admin"
    EXTERNAL_EXAMINER = "external_examiner", "External Examiner"

##User Model
class User(AbstractUser):

    email = models.EmailField(
    unique=True,
    blank=False, 
    null=False
    )

    user_type = models.CharField(
        max_length=30,
        choices=UserType.choices,
        default=UserType.STUDENT
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique = True
    )

    profile_picture = models.ImageField(
       upload_to="profile_pictures/",
        blank=True,
        null=True
    )

    must_change_password = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.user_type})"


##Department Model
class Department(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    code = models.CharField(
        max_length=10,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return f"{self.code} - {self.name}"
    

##Program Model
class Program(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    code = models.CharField(
        max_length=20,
        unique=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="programs"
    )
    

    duration_years = models.PositiveSmallIntegerField(
        default=4
    )

    total_semesters = models.PositiveSmallIntegerField(
        default=8
    )

    semester_count_override = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        help_text="Approved exception to the duration-based semester count.",
    )

    semester_exception_approval_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    semester_exception_approval_note = models.TextField(
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Program"
        verbose_name_plural = "Programs"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_years__gte=1),
                name="program_duration_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        semester_count_override__isnull=True,
                        duration_years__lte=4,
                    )
                    | models.Q(
                        semester_count_override__gte=1,
                        semester_count_override__lte=8,
                    )
                ),
                name="program_effective_semesters_in_catalog",
            ),
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(semester_count_override__isnull=True)
                        & (
                            models.Q(semester_exception_approval_reference__isnull=True)
                            | models.Q(semester_exception_approval_reference="")
                        )
                        & (
                            models.Q(semester_exception_approval_note__isnull=True)
                            | models.Q(semester_exception_approval_note="")
                        )
                    )
                    | (
                        models.Q(semester_count_override__isnull=False)
                        & models.Q(semester_exception_approval_reference__isnull=False)
                        & ~models.Q(semester_exception_approval_reference="")
                        & models.Q(semester_exception_approval_note__isnull=False)
                        & ~models.Q(semester_exception_approval_note="")
                    )
                ),
                name="program_semester_override_requires_approval",
            ),
        ]

    @property
    def effective_semester_count(self):
        if self.semester_count_override is not None:
            return self.semester_count_override
        return self.duration_years * 2

    def clean(self):
        super().clean()
        errors = {}

        if self.duration_years is None or self.duration_years <= 0:
            errors["duration_years"] = "Program duration must be positive."

        effective_count = (
            self.semester_count_override
            if self.semester_count_override is not None
            else (self.duration_years or 0) * 2
        )
        if effective_count <= 0 or effective_count > 8:
            errors["semester_count_override"] = (
                "The effective semester count must be between 1 and 8. "
                "Programs longer than four years need an approved override."
            )

        reference = self.semester_exception_approval_reference or ""
        note = self.semester_exception_approval_note or ""
        has_reference = bool(reference.strip())
        has_note = bool(note.strip())
        if self.semester_count_override is not None and not (has_reference and has_note):
            errors["semester_exception_approval_reference"] = (
                "An override requires an approval reference and note."
            )
        elif self.semester_count_override is None and (reference or note):
            errors["semester_count_override"] = (
                "Approval metadata can only be supplied with a semester override."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"

##Semester Model
class Semester(models.Model):

    number = models.PositiveSmallIntegerField(
        unique=True
    )

    title = models.CharField(
        max_length=30
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return self.title

##AcademicSession Model
class AcademicSession(models.Model):
    SESSION_TYPES = [
        ("spring", "Spring"),
        ("fall", "Fall"),
    ]

    title = models.CharField(
        max_length=50,
        unique=True
    )

    session_type = models.CharField(
        max_length=10,
        choices=SESSION_TYPES
    )

    start_date = models.DateField()

    end_date = models.DateField()

    is_current = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["-start_date"]

        constraints = [
        models.UniqueConstraint(
            fields=["title"],
            name="unique_session_title"
        )
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        errors = {}

        # Existing legacy rows may be invalid. Allow unrelated edits and
        # corrections, but reject new or changed calendar configurations that
        # do not follow the university's Spring/Fall dates.
        check_calendar = self.pk is None
        if self.pk is not None:
            previous = (
                AcademicSession.objects.filter(pk=self.pk)
                .values("session_type", "start_date", "end_date")
                .first()
            )
            check_calendar = previous is None or any(
                previous[field] != getattr(self, field)
                for field in ("session_type", "start_date", "end_date")
            )

        if check_calendar:
            if self.session_type == "spring":
                if self.start_date and self.start_date != self.start_date.replace(
                    month=2, day=1
                ):
                    errors["start_date"] = "Spring must start on February 1."
                if self.end_date and self.start_date and self.end_date != self.start_date.replace(
                    month=7, day=31
                ):
                    errors["end_date"] = "Spring must end on July 31 of the same year."
            elif self.session_type == "fall":
                if self.start_date and self.start_date != self.start_date.replace(
                    month=9, day=1
                ):
                    errors["start_date"] = "Fall must start on September 1."
                if self.end_date and self.start_date:
                    expected_end = self.start_date.replace(
                        year=self.start_date.year + 1, month=1, day=31
                    )
                    if self.end_date != expected_end:
                        errors["end_date"] = (
                            "Fall must end on January 31 of the following year."
                        )
            else:
                errors["session_type"] = "Only Spring and Fall sessions are allowed."

        if self.is_current:
            already_current = (
                self.pk is not None
                and AcademicSession.objects.filter(
                    pk=self.pk, is_current=True
                ).exists()
            )
            if not already_current and AcademicSession.objects.filter(
                is_current=True
            ).exclude(pk=self.pk).exists():
                errors["is_current"] = (
                    "Another academic session is already marked current. "
                    "Resolve the existing current-session records first."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


##office Model
class Office(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    code = models.CharField(
        max_length=15,
        unique=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="offices",
        blank=True,
        null=True
    )

    office_location = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    contact_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Office"
        verbose_name_plural = "Offices"

    def __str__(self):
        return self.name


##Batch Model
class Batch(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True
    )

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="batches"
   )

    admission_year = models.PositiveIntegerField()

    graduation_year = models.PositiveIntegerField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-admission_year", "name"]
        verbose_name = "Batch"
        verbose_name_plural = "Batches"

    def __str__(self):
        return f"{self.name} ({self.program.code})"

    def clean(self):
        if self.graduation_year <= self.admission_year:
            raise ValidationError(
               "Graduation year must be greater than admission year."
        )


##StudentProfile Model
class StudentProfile(models.Model):

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )

    registration_number = models.CharField(
        max_length=30,
        unique=True
    )

    program = models.ForeignKey(
        Program,
        on_delete=models.PROTECT,
        related_name="students"
    )

    batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        related_name="students"
    )

    current_semester = models.ForeignKey(
        Semester,
        on_delete=models.PROTECT,
        related_name="students"
    )

    academic_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.PROTECT,
        related_name="students"
    )

    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    emergency_contact = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    guardian_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    guardian_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    profile_completed = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["registration_number"]
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"

    def __str__(self):
        return f"{self.registration_number} - {self.user.get_full_name() or self.user.username}"

    def clean(self):
        if self.cgpa < 0 or self.cgpa > 4:
            raise ValidationError(
              "CGPA must be between 0.00 and 4.00."
        )

    def save(self, *args, **kwargs):
        if not self.registration_number:
            session_type = self.academic_session.session_type.upper()
            year = str(self.academic_session.start_date.year)[-2:]
            program_code = self.program.code.upper()

            prefix = f"{session_type[:2]}{year}-{program_code}"

            last_student = (
                StudentProfile.objects
                .filter(registration_number__startswith=prefix + "-")
                .order_by("-registration_number")
                .first()
            )

            if last_student:
                last_number = int(
                    last_student.registration_number.split("-")[-1]
                )
                next_number = last_number + 1
            else:
                next_number = 1

            self.registration_number = (
                f"{prefix}-{next_number:03d}"
            )

        super().save(*args, **kwargs)



##FacultyProfile Model
class FacultyProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="faculty_profile"
    )

    employee_id = models.CharField(
        max_length=30,
        unique=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="faculty_members"
    )

    designation = models.CharField(
        max_length=100
    )

    address = models.TextField(
        blank=True,
        null=True,
    )

    specialization = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    office = models.ForeignKey(
        Office,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faculty_members"
    )

    email_extension = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    is_available_for_supervision = models.BooleanField(
        default=True
    )

    max_fyp_groups = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1)]
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["employee_id"]
        verbose_name = "Faculty Profile"
        verbose_name_plural = "Faculty Profiles"

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"


##StaffProfile Model
class StaffProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff_profile"
    )

    employee_id = models.CharField(
        max_length=30,
        unique=True
    )

    office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        related_name="staff_members"
    )

    designation = models.CharField(
        max_length=100
    )

    address = models.TextField(
        blank=True,
        null=True,
    )

    joining_date = models.DateField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["employee_id"]
        verbose_name = "Staff Profile"
        verbose_name_plural = "Staff Profiles"

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"



##ResponsibilityAssignment Model
class ResponsibilityAssignment(models.Model):

    class ResponsibilityType(models.TextChoices):
        ADVISOR = "advisor", "Advisor"
        HOD = "hod", "Head of Department"
        FYP_COORDINATOR = "fyp_coordinator", "FYP Coordinator"
        SCHOLARSHIP_COORDINATOR = "scholarship_coordinator", "Scholarship Coordinator"
        INTERNSHIP_COORDINATOR = "internship_coordinator", "Internship Coordinator"
        EXAM_OFFICER = "exam_officer", "Examination Officer"
        FINANCE_OFFICER = "finance_officer", "Finance Officer"
        STUDENT_AFFAIRS_OFFICER = "student_affairs_officer", "Student Affairs Officer"

    faculty = models.ForeignKey(
        FacultyProfile,
        on_delete=models.CASCADE,
        related_name="responsibilities",
        blank=True,
        null=True
    )

    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="responsibilities",
        blank=True,
        null=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="responsibilities",
        blank=True,
        null=True
    )

    office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        related_name="responsibilities",
        blank=True,
        null=True
    )

    batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        related_name="responsibilities",
        blank=True,
        null=True
    )

    responsibility_type = models.CharField(
        max_length=50,
        choices=ResponsibilityType.choices
    )

    start_date = models.DateField()

    end_date = models.DateField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["responsibility_type", "start_date"]
        verbose_name = "Responsibility Assignment"
        verbose_name_plural = "Responsibility Assignments"

    def clean(self):
        super().clean()

        # At least one person must be assigned
        if not self.faculty and not self.staff:
            raise ValidationError(
                "Assign either a Faculty member or a Staff member."
            )

        # Only one person can be assigned
        if self.faculty and self.staff:
            raise ValidationError(
                "A responsibility can be assigned to either Faculty or Staff, not both."
            )

        # End date must be after start date
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                "End date cannot be earlier than start date."
            )

    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)
        
        

    def __str__(self):
        person = self.faculty if self.faculty else self.staff
        return f"{person} - {self.get_responsibility_type_display()}"
