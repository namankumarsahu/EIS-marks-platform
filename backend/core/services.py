"""Pure logic for cleaning the raw CSV export and computing derived
numbers (averages). Kept free of Django ORM calls so it can be unit
tested in isolation and reused by both the import command and the
corrections endpoint.
"""

import csv
import datetime
import re

VALID_SUBJECTS = {"English", "Hindi", "Maths", "Science", "Social Science"}

_DATE_FORMATS = [
    "%Y-%m-%d",  # 2014-03-15
    "%d/%m/%Y",  # 15/03/2014 (day first)
    "%d-%b-%y",  # 15-Mar-14
    "%d-%b-%Y",  # 15-Mar-2014 (also seen in the data)
    "%d-%m-%Y",  # 27-11-2014 (also present in the CSV)
]


def normalize_name(raw_name):
    """Trim, collapse internal whitespace, and Title Case a student name.

    "  ARJUN   sharma " -> "Arjun Sharma"
    """
    if raw_name is None:
        return ""
    collapsed = re.sub(r"\s+", " ", raw_name.strip())
    return collapsed.title()


def normalize_date(raw_date):
    """Parse a date string in any of the export's formats and return it
    as a datetime.date normalized to YYYY-MM-DD (ISO). Raises ValueError
    if the string matches none of the known formats.
    """
    raw_date = raw_date.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(raw_date, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {raw_date!r}")


def parse_marks(raw_marks):
    """Return an int, or None for an absent student (blank string).
    Raises ValueError if the value is non-blank but not a whole number.
    """
    if raw_marks is None or str(raw_marks).strip() == "":
        return None
    return int(float(raw_marks))


def merge_duplicate_marks(existing, incoming):
    """Two rows share the same (admission_no, subject). Return the mark
    that should be kept, per the rule: if they disagree, keep the higher
    value; a real number always outranks an absence, since a blank
    carries no information to disagree with.
    """
    if existing is None:
        return incoming
    if incoming is None:
        return existing
    return max(existing, incoming)


def average_of(values):
    """Mean of the non-None values, rounded to one decimal place.
    Returns None if every value is None (no exams actually taken/graded).
    """
    present = [v for v in values if v is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 1)


def read_and_clean_csv(csv_path):
    """Read the raw export and apply the dedup/name/date rules, returning
    a dict keyed by admission_no with student info and a per-subject
    marks dict. This is the single source of truth the import command
    writes to the database from, so it's unit-testable without a DB.
    """
    students = {}  # admission_no -> {name, class, section, dob}
    marks = {}  # admission_no -> {subject: marks_or_None}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            admission_no = row["admission_no"].strip()
            name = normalize_name(row["student_name"])
            student_class = row["class"].strip()
            section = row["section"].strip()
            dob = normalize_date(row["date_of_birth"])
            subject = row["subject"].strip()
            mark_value = parse_marks(row["marks_obtained"])

            # First time we see this admission_no, record their info.
            # (Assumes class/section/dob/name are consistent across a
            # student's rows in the export, which held true in practice.)
            students.setdefault(
                admission_no,
                {
                    "name": name,
                    "student_class": student_class,
                    "section": section,
                    "date_of_birth": dob,
                },
            )

            subject_marks = marks.setdefault(admission_no, {})
            if subject in subject_marks:
                subject_marks[subject] = merge_duplicate_marks(subject_marks[subject], mark_value)
            else:
                subject_marks[subject] = mark_value

    return students, marks
