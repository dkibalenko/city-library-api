from django.test import TestCase

from books.models import Book


class BookModelTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="SOFT",
            inventory=10,
            daily_fee=5.99,
        )

    def test_book_str(self):
        self.assertEqual(str(self.book), "Test Book by Test Author")
