from rest_framework import serializers

from .models import Student
from .services import average_of


class StudentListSerializer(serializers.ModelSerializer):
    """Used by GET /api/students/ — one row per student, average computed
    live from their marks so it always reflects the latest corrections.
    """

    average = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ["admission_no", "name", "student_class", "section", "date_of_birth", "average"]

    def get_average(self, obj):
        return average_of([m.marks_obtained for m in obj.marks.all()])


class MarkDetailSerializer(serializers.Serializer):
    subject = serializers.CharField()
    marks_obtained = serializers.IntegerField(allow_null=True)
    max_marks = serializers.IntegerField()


class StudentDetailSerializer(serializers.ModelSerializer):
    """Used by GET /api/students/<admission_no>/ — per-subject marks with
    absents shown as null, plus a total and an average.
    """

    marks = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    average = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "admission_no",
            "name",
            "student_class",
            "section",
            "date_of_birth",
            "marks",
            "total",
            "average",
        ]

    def _mark_values(self, obj):
        return [m.marks_obtained for m in obj.marks.all()]

    def get_marks(self, obj):
        return [
            {
                "subject": m.subject.name,
                "marks_obtained": m.marks_obtained,
                "max_marks": m.max_marks,
            }
            for m in obj.marks.all().order_by("subject__name")
        ]

    def get_total(self, obj):
        present = [v for v in self._mark_values(obj) if v is not None]
        return sum(present) if present else 0

    def get_average(self, obj):
        return average_of(self._mark_values(obj))


class CorrectionInputSerializer(serializers.Serializer):
    """Validates the body of POST /api/marks/corrections/. Cross-field
    checks (admission_no exists, subject is one of the five, marks in
    range) live in the view so we can return the specific 400 reasons
    the checker expects; this serializer only validates shape/types.
    """

    admission_no = serializers.CharField()
    subject = serializers.CharField()
    marks = serializers.IntegerField()
