from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Mark, Student, Subject
from core.services import VALID_SUBJECTS, read_and_clean_csv


class Command(BaseCommand):
    """Loads students_marks.csv into the database, applying the cleaning
    rules (dedup, name casing, date normalization, absent handling).

    Re-runnable by design: it wipes existing Student/Mark/Subject rows
    first, so you always land on the same clean state regardless of how
    many times it's run or what corrections were applied since the last
    run. That's what lets the corrections questions be answered from a
    known "post-import, pre-corrections" baseline.

        python manage.py import_marks path/to/students_marks.csv
    """

    help = "Import and clean the students_marks.csv export (re-runnable, resets prior data)."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            nargs="?",
            default="data/students_marks.csv",
            help="Path to the CSV export (default: data/students_marks.csv)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        students_data, marks_data = read_and_clean_csv(csv_path)

        # Reset to a clean slate so this command can be re-run any time.
        Mark.objects.all().delete()
        Student.objects.all().delete()
        Subject.objects.all().delete()

        subjects = {name: Subject.objects.create(name=name) for name in sorted(VALID_SUBJECTS)}

        created_students = 0
        created_marks = 0

        for admission_no, info in students_data.items():
            student = Student.objects.create(
                admission_no=admission_no,
                name=info["name"],
                student_class=info["student_class"],
                section=info["section"],
                date_of_birth=info["date_of_birth"],
            )
            created_students += 1

            for subject_name, mark_value in marks_data.get(admission_no, {}).items():
                if subject_name not in subjects:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping unknown subject {subject_name!r} for {admission_no}"
                        )
                    )
                    continue
                Mark.objects.create(
                    student=student,
                    subject=subjects[subject_name],
                    marks_obtained=mark_value,
                )
                created_marks += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created_students} students and {created_marks} marks from {csv_path}"
            )
        )
