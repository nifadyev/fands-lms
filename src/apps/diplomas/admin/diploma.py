import datetime

from celery import group
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request

from apps.diplomas.models import Diploma
from apps.orders import tasks
from apps.products.admin.filters import CourseFilter
from apps.products.models import Course
from apps.users.models import User
from core.admin import ModelAdmin, admin


@admin.register(Diploma)
class DiplomaAdmin(ModelAdmin):
    list_display = [
        "date",
        "student",
        "course",
        "language",
        "homework_accepted",
    ]
    fields = [
        "slug",
        "student",
        "study",
        "course",
        "language",
        "image",
    ]
    list_filter = [
        "language",
        CourseFilter,
    ]

    search_fields = [
        "study__student__first_name",
        "study__student__last_name",
        "study__student__email",
    ]
    actions = [
        "send_to_student",
        "regenerate",
    ]

    readonly_fields = ["slug", "course", "student"]
    list_select_related = ["study", "study__student", "study__course"]
    raw_id_fields = ["study"]

    @admin.display(description=_("Student"), ordering="study__student")
    def student(self, diploma: Diploma) -> User:
        return diploma.study.student

    @admin.display(description=_("Course"), ordering="study__course")
    def course(self, diploma: Diploma) -> Course:
        return diploma.study.course

    @admin.display(description=_("Homework"), ordering="study__homework_accepted", boolean=True)
    def homework_accepted(self, diploma: Diploma) -> bool:
        return diploma.study.homework_accepted

    @admin.display(description=_("Date"), ordering="created")
    def date(self, diploma: Diploma) -> datetime.datetime:
        return diploma.modified or diploma.created

    @admin.action(description=_("Send diploma to student"))
    def send_to_student(self, request: Request, queryset: QuerySet) -> None:
        for diploma in queryset.iterator():
            diploma.send_to_student()

        self.message_user(request, f"Diplomas sent to {queryset.count()} students")

    @admin.action(description=_("Regenerate diploma"))
    def regenerate(self, request: Request, queryset: QuerySet) -> None:
        order_ids = queryset.values_list("study__order_id", flat=True).distinct()

        generate_diplomas = group([tasks.generate_diploma.s(order_id=order_id) for order_id in order_ids])
        generate_diplomas.skew(step=2).apply_async()

        self.message_user(request, f"Started generation of {len(order_ids)} diplomas")
