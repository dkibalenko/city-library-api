from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

from rest_framework.exceptions import ValidationError

from borrowings.models import Borrowing
from books.models import Book
from borrowings.serializers import BorrowingSerializer


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
        self.borrowing.expected_return_date = (
            timezone.now() - timezone.timedelta(days=1)
        )
        with self.assertRaises(IntegrityError):
            self.borrowing.save()

    def test_actual_return_date_gte_borrow_date_or_null(self):
        self.borrowing.actual_return_date = (
            timezone.now() - timezone.timedelta(days=1)
        )
        with self.assertRaises(IntegrityError):
            self.borrowing.save()


class BorrowingSerializerTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.book = Book.objects.create(
            title="Sample Book",
            author="Author",
            cover=Book.SOFT,
            inventory=1,
            daily_fee=1.50,
        )
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="password"
        )
        self.borrowing_data = {
            "borrow_date": timezone.now().date(),
            "expected_return_date": (
                timezone.now() + timezone.timedelta(days=7)
            ).date(),
            "book": self.book.id,
            # "user": self.user,
        }
        self.request = self.factory.get("/")
        self.request.user = self.user

    def test_validate_book_inventory(self):
        serializer = BorrowingSerializer(
            data=self.borrowing_data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())

        self.book.inventory = 0
        self.book.save()

        with self.assertRaises(ValidationError):
            serializer = BorrowingSerializer(
                data=self.borrowing_data, context={"request": self.request}
            )
            serializer.is_valid(raise_exception=True)

    def test_successful_create_borrowing_with_atomic_transaction(self):
        serializer = BorrowingSerializer(
            data=self.borrowing_data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        borrowing = serializer.save()

        self.assertEqual(Borrowing.objects.count(), 1)
        self.assertEqual(borrowing.book, self.book)
        self.assertEqual(borrowing.user, self.user)

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 0)

    def test_rollback_create_borrowing_with_atomic_transaction(self):
        original_inventory = self.book.inventory

        try:
            with transaction.atomic():
                serializer1 = BorrowingSerializer(
                    data=self.borrowing_data, context={"request": self.request}
                )
                serializer1.is_valid(raise_exception=True)
                serializer1.save()

                serializer2 = BorrowingSerializer(
                    data=self.borrowing_data, context={"request": self.request}
                )
                serializer2.is_valid(raise_exception=True)
                serializer2.save()

        except ValidationError:
            pass

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, original_inventory)

    def test_create_borrowing_with_db_integrity_error(self):
        try:
            with transaction.atomic():
                invalid_borrowing_data = {
                    "borrow_date": timezone.now().date(),
                    "expected_return_date": (
                        timezone.now() - timezone.timedelta(days=1)
                    ).date(),
                    "book": self.book.id,
                }

                serializer = BorrowingSerializer(
                    data=invalid_borrowing_data,
                    context={"request": self.request}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

        except ValidationError:
            pass

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)

    def test_to_representation(self):
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=timezone.now().date(),
            expected_return_date=(
                timezone.now() + timezone.timedelta(days=7)
            ).date(),
        )

        serializer = BorrowingSerializer(borrowing)
        data = serializer.data

        self.assertEqual(data["book"]["title"], self.book.title)
        self.assertEqual(data["book"]["author"], self.book.author)
        self.assertEqual(data["book"]["cover"], self.book.cover)
        self.assertEqual(data["book"]["inventory"], self.book.inventory)
        self.assertEqual(float(data["book"]["daily_fee"]), self.book.daily_fee)

        self.assertEqual(data["id"], borrowing.id)
        self.assertEqual(data["user_email"], self.user.email)
        self.assertEqual(
            data["borrow_date"],
            borrowing.borrow_date.strftime("%Y-%m-%d"),
        )
        self.assertEqual(
            data["expected_return_date"],
            borrowing.expected_return_date.strftime("%Y-%m-%d"),
        )
        self.assertEqual(
            data["actual_return_date"],
            borrowing.actual_return_date,
        )
