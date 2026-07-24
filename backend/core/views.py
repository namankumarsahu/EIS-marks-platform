from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Mark, Student, Subject
from .serializers import (
    CorrectionInputSerializer,
    StudentDetailSerializer,
    StudentListSerializer,
)
from .services import VALID_SUBJECTS, average_of


class StudentListView(APIView):
    """GET /api/students/?search=<text>
    Case-insensitive substring match on name; returns all students when
    no search term is given.
    """

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        qs = Student.objects.all()
        if search:
            qs = qs.filter(Q(name__icontains=search))
        serializer = StudentListSerializer(qs, many=True)
        return Response(serializer.data)


class StudentDetailView(APIView):
    """GET /api/students/<admission_no>/"""

    def get(self, request, admission_no):
        student = get_object_or_404(Student, admission_no=admission_no)
        serializer = StudentDetailSerializer(student)
        return Response(serializer.data)


class SummaryView(APIView):
    """GET /api/summary/ — class average per subject, and the top student
    by total marks. Computed live from current data (post-corrections).
    """

    def get(self, request):
        subject_averages = {}
        for subject in Subject.objects.all().order_by("name"):
            values = [m.marks_obtained for m in Mark.objects.filter(subject=subject)]
            avg = average_of(values)
            subject_averages[subject.name] = avg

        top_student = None
        best_total = None
        for student in Student.objects.prefetch_related("marks"):
            present = [m.marks_obtained for m in student.marks.all() if m.marks_obtained is not None]
            total = sum(present) if present else 0
            if best_total is None or total > best_total:
                best_total = total
                top_student = student

        top_payload = None
        if top_student is not None:
            top_payload = {
                "admission_no": top_student.admission_no,
                "name": top_student.name,
                "total": best_total,
            }

        return Response(
            {
                "subject_averages": subject_averages,
                "top_student": top_payload,
            }
        )


class MarkCorrectionView(APIView):
    """POST /api/marks/corrections/
    Body: {"admission_no": "EIS-1012", "subject": "Maths", "marks": 88}
    Validates admission_no exists, subject is one of the five known
    subjects, and marks is an integer 0-100. A valid correction
    overwrites the stored mark (including filling in an Absent) and
    returns 200. An invalid one changes nothing and returns 400.
    """

    def post(self, request):
        shape = CorrectionInputSerializer(data=request.data)
        if not shape.is_valid():
            return Response(shape.errors, status=status.HTTP_400_BAD_REQUEST)

        admission_no = shape.validated_data["admission_no"]
        subject_name = shape.validated_data["subject"]
        marks = shape.validated_data["marks"]

        errors = {}

        student = Student.objects.filter(admission_no=admission_no).first()
        if student is None:
            errors["admission_no"] = f"No student with admission_no {admission_no!r}."

        if subject_name not in VALID_SUBJECTS:
            errors["subject"] = f"{subject_name!r} is not one of the five known subjects."

        if not (0 <= marks <= 100):
            errors["marks"] = "marks must be an integer from 0 to 100."

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        subject = Subject.objects.get(name=subject_name)
        mark, _created = Mark.objects.get_or_create(student=student, subject=subject)
        mark.marks_obtained = marks
        mark.save()

        return Response(
            {
                "admission_no": student.admission_no,
                "subject": subject.name,
                "marks": mark.marks_obtained,
            },
            status=status.HTTP_200_OK,
        )
