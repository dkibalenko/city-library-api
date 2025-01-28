from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.urls import reverse

from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from borrowings.models import Borrowing
from books.models import Book
from borrowings.serializers import BorrowingSerializer
from borrowings.views import BorrowingListView, BorrowingReturnView


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


class BorrowingListViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpassword"
        )
        self.user_1 = get_user_model().objects.create_user(
            email="user1@example.com", password="user1password"
        )
        self.user_2 = get_user_model().objects.create_user(
            email="user2@example.com", password="user2password"
        )
        self.book = Book.objects.create(
            title="Sample Book",
            author="Author",
            cover=Book.SOFT,
            inventory=1,
            daily_fee=1.50,
        )
        self.borrowing_1 = Borrowing.objects.create(
            book=self.book,
            user=self.user_1,
            borrow_date="2025-01-01",
            expected_return_date="2025-01-10"
        )
        self.borrowing_2 = Borrowing.objects.create(
            book=self.book,
            user=self.user_2,
            borrow_date="2025-01-05",
            expected_return_date="2025-01-15",
            actual_return_date="2025-01-12",
        )

    def test_init_method_initialize_queryset(self):
        view = BorrowingListView()
        self.assertIsNotNone(view.queryset)
        self.assertEqual(list(view.queryset), list(Borrowing.objects.all()))

    def test_get_queryset_superuser(self):
        request = APIRequestFactory().get("/borrowings/")
        force_authenticate(request, user=self.admin_user)
        view = BorrowingListView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["id"], self.borrowing_1.id)
        self.assertEqual(response.data[1]["id"], self.borrowing_2.id)

    def test_get_queryset_regular_user(self):
        request = APIRequestFactory().get("/borrowings/")
        force_authenticate(request, user=self.user_1)
        view = BorrowingListView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.borrowing_1.id)

    def test_get_queryset_user_filtered_by_is_active(self):
        request = APIRequestFactory().get("/borrowings/?is_active=true")
        force_authenticate(request, user=self.user_1)
        view = BorrowingListView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user_email"], self.user_1.email)

    def test_get_queryset_user_filtered_by_is_not_active(self):
        request = APIRequestFactory().get("/borrowings/?is_active=false")
        force_authenticate(request, user=self.user_2)
        view = BorrowingListView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user_email"], self.user_2.email)

    def test_get_queryset_superuser_filtered_by_user_id(self):
        request = APIRequestFactory().get(
            f"/borrowings/?user_id={self.user_1.id}"
        )
        force_authenticate(request, user=self.admin_user)
        view = BorrowingListView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user_email"], self.user_1.email)


class BorrowingReturnViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            email="testuser@example", password="testpass"
        )
        self.book = Book.objects.create(
            title="Sample Book",
            author="Author",
            cover=Book.SOFT,
            inventory=1,
            daily_fee=1.50,
        )
        self.borrowing = Borrowing.objects.create(
            borrow_date=timezone.now().date(),
            expected_return_date=(
                timezone.now().date() + timezone.timedelta(days=7)
            ),
            book=self.book,
            user=self.user
        )

    def test_get_borrowing(self):
        request = self.factory.get(f"/borrowings/{self.borrowing.id}/return/")
        force_authenticate(request, user=self.user)
        view = BorrowingReturnView.as_view()
        response = view(request, pk=self.borrowing.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.borrowing.id)

    def test_successful_post_return_borrowing_with_actual_return_date(self):
        request = self.factory.post(f"/borrowings/{self.borrowing.id}/return/")
        force_authenticate(request, user=self.user)
        view = BorrowingReturnView.as_view()
        response = view(request, pk=self.borrowing.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.borrowing.id)
        self.assertEqual(
            response.data["actual_return_date"],
            timezone.now().date().isoformat()
        )
