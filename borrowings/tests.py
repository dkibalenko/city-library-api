from django.test import TestCase
from django.utils import timezone
from django.db.utils import IntegrityError

from django.contrib.auth import get_user_model

from borrowings.models import Borrowing
from books.models import Book


class BorrowingModelTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Sample Book",
            author="Author",
            cover=Book.SOFT,
            inventory=5,
            daily_fee=1.50,
        )
        self.user = get_user_model().objects.create_user(
            email="user@example", password="userpassword"
        )
        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=timezone.now(),
            expected_return_date=timezone.now() + timezone.timedelta(days=7),
        )

    def test_borrowing_str(self):
        expected_str = f"{self.book.title} borrowed by {self.user.email}"
        self.assertEqual(str(self.borrowing), expected_str)

    def test_borrow_date_lte_expected_return_date(self):
        self.borrowing.expected_return_date = timezone.now() - \
            timezone.timedelta(days=1)
        with self.assertRaises(IntegrityError):
            self.borrowing.save()

    def test_actual_return_date_gte_borrow_date_or_null(self):
        self.borrowing.actual_return_date = timezone.now() - \
            timezone.timedelta(days=1)
        with self.assertRaises(IntegrityError):
            self.borrowing.save()
