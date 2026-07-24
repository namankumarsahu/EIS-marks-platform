import datetime

from django.test import TestCase

from core.models import Mark, Student, Subject


class StudentModelTests(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            admission_no="EIS-2001",
            name="Test Student",
            student_class="6",
            section="A",
            date_of_birth=datetime.date(2014, 1, 1),
        )
        self.subject = Subject.objects.create(name="Maths")

    def test_str_representation(self):
        self.assertIn("EIS-2001", str(self.student))

    def test_admission_no_is_unique(self):
        with self.assertRaises(Exception):
            Student.objects.create(
                admission_no="EIS-2001",
                name="Duplicate",
                student_class="6",
                section="B",
                date_of_birth=datetime.date(2014, 1, 1),
            )


class MarkModelTests(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            admission_no="EIS-2002",
            name="Test Student Two",
            student_class="6",
            section="A",
            date_of_birth=datetime.date(2014, 1, 1),
        )
        self.subject = Subject.objects.create(name="Science")

    def test_is_absent_true_when_marks_none(self):
        mark = Mark.objects.create(student=self.student, subject=self.subject, marks_obtained=None)
        self.assertTrue(mark.is_absent)

    def test_is_absent_false_when_marks_present(self):
        mark = Mark.objects.create(student=self.student, subject=self.subject, marks_obtained=80)
        self.assertFalse(mark.is_absent)

    def test_unique_student_subject_constraint(self):
        Mark.objects.create(student=self.student, subject=self.subject, marks_obtained=80)
        with self.assertRaises(Exception):
            Mark.objects.create(student=self.student, subject=self.subject, marks_obtained=90)
