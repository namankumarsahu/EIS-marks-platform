from django.contrib import admin

from .models import Mark, Student, Subject


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["admission_no", "name", "student_class", "section", "date_of_birth"]
    search_fields = ["admission_no", "name"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ["student", "subject", "marks_obtained", "max_marks"]
    list_filter = ["subject"]
