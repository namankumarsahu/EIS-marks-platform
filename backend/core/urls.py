from django.urls import path

from .views import MarkCorrectionView, StudentDetailView, StudentListView, SummaryView

urlpatterns = [
    path("students/", StudentListView.as_view(), name="student-list"),
    path("students/<str:admission_no>/", StudentDetailView.as_view(), name="student-detail"),
    path("summary/", SummaryView.as_view(), name="summary"),
    path("marks/corrections/", MarkCorrectionView.as_view(), name="mark-correction"),
]
