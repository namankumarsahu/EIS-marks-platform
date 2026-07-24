import datetime

from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Mark, Student, Subject


class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.maths = Subject.objects.create(name="Maths")
        self.science = Subject.objects.create(name="Science")

        self.arjun = Student.objects.create(
            admission_no="EIS-3001",
            name="Arjun Sharma",
            student_class="6",
            section="A",
            date_of_birth=datetime.date(2014, 3, 15),
        )
        self.diya = Student.objects.create(
            admission_no="EIS-3002",
            name="Diya Joshi",
            student_class="6",
            section="B",
            date_of_birth=datetime.date(2014, 2, 13),
        )

        Mark.objects.create(student=self.arjun, subject=self.maths, marks_obtained=80)
        Mark.objects.create(student=self.arjun, subject=self.science, marks_obtained=None)  # absent
        Mark.objects.create(student=self.diya, subject=self.maths, marks_obtained=90)
        Mark.objects.create(student=self.diya, subject=self.science, marks_obtained=70)


class StudentListViewTests(BaseAPITestCase):
    def test_returns_all_students_without_search(self):
        response = self.client.get(reverse("student-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_case_insensitive_substring_search(self):
        response = self.client.get(reverse("student-list"), {"search": "arjun"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["admission_no"], "EIS-3001")

    def test_search_matches_partial_name(self):
        response = self.client.get(reverse("student-list"), {"search": "jo"})
        # matches both "Sharma"? no -- matches "Joshi"
        names = [row["name"] for row in response.data]
        self.assertIn("Diya Joshi", names)

    def test_average_excludes_absent(self):
        response = self.client.get(reverse("student-list"), {"search": "Arjun"})
        # Arjun: Maths 80, Science absent -> average is just 80.0
        self.assertEqual(response.data[0]["average"], 80.0)


class StudentDetailViewTests(BaseAPITestCase):
    def test_detail_includes_absent_as_null(self):
        response = self.client.get(reverse("student-detail", args=["EIS-3001"]))
        self.assertEqual(response.status_code, 200)
        science_row = next(m for m in response.data["marks"] if m["subject"] == "Science")
        self.assertIsNone(science_row["marks_obtained"])

    def test_detail_total_and_average(self):
        response = self.client.get(reverse("student-detail", args=["EIS-3002"]))
        self.assertEqual(response.data["total"], 160)
        self.assertEqual(response.data["average"], 80.0)

    def test_unknown_admission_no_404(self):
        response = self.client.get(reverse("student-detail", args=["EIS-9999"]))
        self.assertEqual(response.status_code, 404)


class SummaryViewTests(BaseAPITestCase):
    def test_subject_averages(self):
        response = self.client.get(reverse("summary"))
        self.assertEqual(response.data["subject_averages"]["Maths"], 85.0)
        self.assertEqual(response.data["subject_averages"]["Science"], 70.0)

    def test_top_student_by_total(self):
        response = self.client.get(reverse("summary"))
        self.assertEqual(response.data["top_student"]["admission_no"], "EIS-3002")
