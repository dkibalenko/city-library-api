from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer


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
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
