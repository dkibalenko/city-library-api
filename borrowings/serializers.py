from django.db import IntegrityError, transaction

from rest_framework import serializers

from borrowings.models import Borrowing, Book
from books.serializers import BookSerializer
from borrowings.telegram_bot import send_telegram_message


class BorrowingSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
    )
    user_email = serializers.StringRelatedField(source="user.email")
    is_active = serializers.SerializerMethodField()

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

    def get_is_active(self, obj):
        return obj.actual_return_date is None

    def validate_book(self, value):
        if value.inventory <= 0:
            raise serializers.ValidationError("Book is not available")
        return value

    def create(self, validated_data):
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

    def to_representation(self, instance):
        """
        Customize the representation of Borrowing objects by including the
        book's representation (using BookSerializer) instead of just the book's
        id.
        """
        representation = super().to_representation(instance)
        representation["book"] = BookSerializer(instance.book).data
        return representation


class BorrowingDetailSerializer(BorrowingSerializer):
    actual_return_date = serializers.DateField(required=False)
    book = BookSerializer(read_only=True)

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
    actual_return_date = serializers.DateField(read_only=True)

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
