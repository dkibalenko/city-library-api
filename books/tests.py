from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status

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


class BookViewSetTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="userpassword"
        )
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpassword"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="SOFT",
            inventory=10,
            daily_fee=5.99,
        )

    def test_anyone_can_list_books(self):
        response = self.client.get(reverse("books:book-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anyone_can_reteive_book(self):
        response = self.client.get(
            reverse(
                "books:book-detail",
                args=[self.book.id])
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.book.id)
        
    def test_non_admin_user_cannot_perform_create_book(self):
        self.client.force_authenticate(user=self.user)
        pay_load = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": 5.99,
        }
        response = self.client.post(
            reverse("books:book-list"),
            data=pay_load
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_user_cannot_perform_update_book(self):
        self.client.force_authenticate(user=self.user)
        pay_load = {
            "title": "Update Test Book",
            "author": "Updte Test Author",
            "cover": "HARD",
            "inventory": 10,
            "daily_fee": 5.99,
        }
        response = self.client.put(
            reverse(
                "books:book-detail",
                args=[self.book.id]
            ),
            data=pay_load
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

 
    def test_non_admin_user_cannot_perform_delete_book(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse(
                "books:book-detail",
                args=[self.book.id]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_admin_user_can_perform_create_book(self):
        self.client.force_authenticate(user=self.admin_user)
        pay_load = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": 5.99,
        }
        response = self.client.post(
            reverse("books:book-list"),
            data=pay_load
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], pay_load["title"])

    def test_admin_user_can_perform_update_book(self):
        self.client.force_authenticate(user=self.admin_user)
        pay_load = {
            "title": "Update Test Book",
            "author": "Updte Test Author",
            "cover": "HARD",
            "inventory": 10,
            "daily_fee": 5.99,
        }
        response = self.client.put(
            reverse(
                "books:book-detail",
                args=[self.book.id]
            ),
            data=pay_load
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], pay_load["title"])

    def test_admin_user_can_perform_delete_book(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(
            reverse(
                "books:book-detail",
                args=[self.book.id]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=self.book.id).exists())
