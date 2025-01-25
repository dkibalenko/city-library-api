from django.db import IntegrityError, transaction

from rest_framework import serializers

from borrowings.models import Borrowing, Book
from books.serializers import BookSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
    )
    user_email = serializers.StringRelatedField(source="user.email")

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "book",
            "user_email",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        )
        
        depth = 1

    def validate_book(self, value):
        if value.inventory <= 0:
            raise serializers.ValidationError("Book is not available")
        return value

    def create(self, validated_data):
        with transaction.atomic():
            book = validated_data.pop("book")
            user = self.context["request"].user
            try:
                borrowing = Borrowing.objects.create(
                    book=book, user=user, **validated_data
                )
                book.inventory -= 1
                book.save()
                return borrowing
            except IntegrityError as e:
                raise serializers.ValidationError(
                    f"Failed to create borrowing due to integrity error: {e}"
                )

    def to_representation(self, instance):
        """
        Customize the representation of Borrowing objects by including the
        book's representation (using BookSerializer) instead of just the book's
        id.
        """
        representation = super().to_representation(instance)
        representation["book"] = BookSerializer(instance.book).data
        return representation
