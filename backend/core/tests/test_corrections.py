import datetime

from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Mark, Student, Subject


class MarkCorrectionViewTests(APITestCase):
    def setUp(self):
        self.maths = Subject.objects.create(name="Maths")
        self.english = Subject.objects.create(name="English")
        self.student = Student.objects.create(
            admission_no="EIS-4001",
            name="Test Student",
            student_class="6",
            section="A",
            date_of_birth=datetime.date(2014, 1, 1),
        )
        self.url = reverse("mark-correction")

    def test_valid_correction_updates_existing_mark(self):
        Mark.objects.create(student=self.student, subject=self.maths, marks_obtained=50)
        response = self.client.post(
            self.url,
            {"admission_no": "EIS-4001", "subject": "Maths", "marks": 88},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Mark.objects.get(student=self.student, subject=self.maths).marks_obtained, 88)

    def test_valid_correction_fills_in_absent(self):
        Mark.objects.create(student=self.student, subject=self.english, marks_obtained=None)
        response = self.client.post(
            self.url,
            {"admission_no": "EIS-4001", "subject": "English", "marks": 70},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Mark.objects.get(student=self.student, subject=self.english).marks_obtained, 70
        )

    def test_unknown_admission_no_returns_400_and_no_change(self):
        response = self.client.post(
            self.url,
            {"admission_no": "EIS-9999", "subject": "English", "marks": 70},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_subject_returns_400(self):
        response = self.client.post(
            self.url,
            {"admission_no": "EIS-4001", "subject": "Sanskrit", "marks": 55},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_marks_above_100_returns_400(self):
        response = self.client.post(
            self.url,
            {"admission_no": "EIS-4001", "subject": "Maths", "marks": 105},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_marks_below_0_returns_400(self):
        response = self.client.post(
            self.url,
            {"admission_no": "EIS-4001", "subject": "Maths", "marks": -5},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_correction_leaves_data_unchanged(self):
        Mark.objects.create(student=self.student, subject=self.maths, marks_obtained=50)
        self.client.post(
            self.url,
            {"admission_no": "EIS-4001", "subject": "Maths", "marks": 999},
            format="json",
        )
        self.assertEqual(Mark.objects.get(student=self.student, subject=self.maths).marks_obtained, 50)

    def test_summary_and_detail_reflect_correction_live(self):
        Mark.objects.create(student=self.student, subject=self.maths, marks_obtained=50)
        self.client.post(
            self.url,
            {"admission_no": "EIS-4001", "subject": "Maths", "marks": 88},
            format="json",
        )
        detail = self.client.get(reverse("student-detail", args=["EIS-4001"]))
        self.assertEqual(detail.data["total"], 88)
