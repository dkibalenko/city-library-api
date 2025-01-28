from django.db import transaction
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingDetailSerializer,
    BorrowingReturnSerializer
)


class BorrowingListView(generics.ListCreateAPIView):
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = Borrowing.objects.all()

    def get_queryset(self):
        queryset = self.queryset
        is_active = self.request.query_params.get("is_active", None)
        user_id = self.request.query_params.get("user_id", None)

        if is_active:
            is_active_bool = is_active.lower() == "true"
            queryset = queryset.filter(
                actual_return_date__isnull=is_active_bool
            )

        if self.request.user.is_superuser:
            if user_id:
                queryset = queryset.filter(user=user_id)
            return queryset

        return queryset.filter(user=self.request.user)


class BorrowingDetailView(generics.RetrieveAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingDetailSerializer
    permission_classes = [IsAuthenticated]


class BorrowingReturnView(generics.GenericAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingReturnSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        borrowing = self.get_object()
        serializer = self.get_serializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk, forma=None):
        with transaction.atomic():
            borrowing = self.queryset.get(pk=pk)
            borrowing.actual_return_date = timezone.now().date()
            borrowing.book.inventory += 1
            borrowing.book.save()
            borrowing.save()
        serializer = self.get_serializer(borrowing)
        return Response(serializer.data)
