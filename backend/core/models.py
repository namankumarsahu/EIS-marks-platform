from django.db import models


class Student(models.Model):
    """One row per student. admission_no is the natural/business key from
    the school ERP, so it's kept unique and is what the API and the
    corrections endpoint key off (rather than the internal numeric id).
    """
    

    admission_no = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    student_class = models.CharField(max_length=10)
    section = models.CharField(max_length=5)
    date_of_birth = models.DateField()

    class Meta:
        ordering = ["admission_no"]

    def __str__(self):
        return f"{self.admission_no} - {self.name}"


class Subject(models.Model):
    """Kept as its own table (rather than a free-text field on Mark) so
    the set of five subjects is a real, enforceable list and typos can't
    silently create a sixth subject.
    """

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Mark(models.Model):
    """One row per (student, subject). marks_obtained is nullable — a
    NULL means the student was absent for that exam, which is distinct
    from a genuine zero and must never be averaged in as zero.
    """

    student = models.ForeignKey(Student, related_name="marks", on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, related_name="marks", on_delete=models.CASCADE)
    marks_obtained = models.PositiveSmallIntegerField(null=True, blank=True)
    max_marks = models.PositiveSmallIntegerField(default=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "subject"], name="unique_student_subject")
        ]
        ordering = ["subject__name"]

    def __str__(self):
        shown = "Absent" if self.marks_obtained is None else self.marks_obtained
        return f"{self.student.admission_no} / {self.subject.name}: {shown}"

    @property
    def is_absent(self):
        return self.marks_obtained is None
