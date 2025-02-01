from django.db import IntegrityError, transaction

from rest_framework import serializers

from borrowings.models import Borrowing, Book
from books.serializers import BookSerializer
from borrowings.telegram_bot import send_telegram_message


class BorrowingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Borrowing model.
    """
    book = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        help_text="ID of the book to borrow",
    )
    user_email = serializers.StringRelatedField(
        read_only=True,
        source="user.email",
        help_text="Email of the user who borrowed the book",
    )
    is_active = serializers.SerializerMethodField(
        help_text="Indicates if the borrowing is active (not returned)."
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "book",
            "user_email",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "is_active",
        )

        depth = 1

        read_only_fields = (
            "id",
            "actual_return_date",
        )

    def get_is_active(self, obj) -> bool:
        return obj.actual_return_date is None

    def validate_book(self, value) -> Book:
        if value.inventory <= 0:
            raise serializers.ValidationError("Book is not available")
        return value

    def create(self, validated_data) -> Borrowing:
        book = validated_data.pop("book")
        user = self.context["request"].user
        borrowing = None

        with transaction.atomic():
            try:
                borrowing = Borrowing.objects.create(
                    book=book, user=user, **validated_data
                )
                book.inventory -= 1
                book.save()
            except IntegrityError as e:
                raise serializers.ValidationError(
                    f"Failed to create borrowing due to integrity error: {e}"
                )
            
        if borrowing:
            message = f"""
                <b>New Borrowing Created:</b>
                <pre>User: {user.email}</pre>
                <pre>Book: {book.title}</pre>
                <pre>Borrow Date: {borrowing.borrow_date}</pre>
                <pre>
                    Expected Return Date: {borrowing.expected_return_date}
                </pre>
            """
            send_telegram_message(message)

        return borrowing

    def to_representation(self, instance) -> dict:
        """
        Customize the representation of Borrowing objects by including the
        book's representation (using BookSerializer) instead of just the book's
        id.
        """
        representation = super().to_representation(instance)
        representation["book"] = BookSerializer(instance.book).data
        return representation


class BorrowingDetailSerializer(BorrowingSerializer):
    """
    Serializer for the borrowing details, should be used in GET requests
    for getting specific borrowing
    """
    actual_return_date = serializers.DateField(
        required=False,
        help_text="Date when the book was returned",
    )
    book = BookSerializer(
        read_only=True,
        help_text="Details of the book borrowed",
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "book",
            "user_email",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "is_active",
        )
        depth = 1

        read_only_fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "user_email",
            "is_active",
        )


class BorrowingReturnSerializer(BorrowingDetailSerializer):
    """
    Serializer for the borrowing return, should be used in POST requests
    for returning specific borrowing
    """
    actual_return_date = serializers.DateField(
        read_only=True,
        help_text="Date when the book was returned",
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        )

        read_only_fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        )
