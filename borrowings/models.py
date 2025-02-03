from django.db import models
from django.conf import settings
from django.db.models import Q, F, CheckConstraint

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.book.title} borrowed by {self.user.email}"

    class Meta:
        ordering = ["borrow_date"]
        constraints = [
            CheckConstraint(
                check=Q(borrow_date__lte=F("expected_return_date")),
                name="check_borrow_date_lte_expected_return_date",
            ),
            CheckConstraint(
                check=Q(actual_return_date__gte=F("borrow_date"))
                | Q(actual_return_date__isnull=True),
                name="check_actual_return_date_gte_borrow_date_or_null",
            ),
        ]
