from django.db import transaction
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    OpenApiRequest
)
from drf_spectacular.types import OpenApiTypes

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingDetailSerializer,
    BorrowingReturnSerializer
)


class BorrowingListView(generics.ListCreateAPIView):
    """
    This endpoint provides a list of all borrowings.
    It allows filtering by active status and user ID.
    It also allows creation of new borrowing instances.
    """
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = Borrowing.objects.all()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.STR,
                description="Filter borrowings based on whether they are \
                    currently active (not returned). Possible values: 'true'\
                    or 'false'.",
                required=False,
                examples=[
                    OpenApiExample(
                        "active",
                        value="true",
                        summary="Active borrowings"
                    ),
                    OpenApiExample(
                        "returned", 
                        value="false", 
                        summary="Returned borrowings"
                    ),
                ]
            ),
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                description="Filter by a specific user id, available only \
                    for superusers",
                required=False,
                examples=[
                    OpenApiExample(
                        "user_id_example",
                        value=5,
                        summary="Filter by user ID"
                    ),
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="List of borrowings",
                response=BorrowingSerializer,
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value=[
                            {
                                "id": 1,
                                "book": {
                                    "id": 1,
                                    "title": "Sample Book",
                                    "author": "Author",
                                    "cover": "HARD",
                                    "inventory": 1,
                                    "daily_fee": 1.50,
                                },
                                "user_email": "user@example.com",
                                "borrow_date": "2023-01-01",
                                "expected_return_date": "2023-01-08",
                                "actual_return_date": None,
                                "is_active": True
                            }
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                response=BorrowingSerializer,
                examples=[
                    OpenApiExample(
                        name="Unauthorized response",
                        value={
                            "detail": "Authentication credentials were \
                                not provided."
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Forbidden",
                response=BorrowingSerializer,
                examples=[
                    OpenApiExample(
                        name="Forbidden response",
                        value={
                            "detail": "You do not have permission to perform \
                                this action."
                        }
                    )
                ]
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        methods=["post"],
        request=OpenApiRequest(
            request=BorrowingSerializer,
            examples=[
                OpenApiExample(
                    name="Borrowing creation example",
                    value={
                        "book": 1,
                        "borrow_date": "2023-01-01",
                        "expected_return_date": "2023-01-08"
                    }
                )
            ]
        ),
        responses={
            201: OpenApiResponse(
                description="Borrowing created successfully",
                response=BorrowingSerializer,
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "id": 1,
                            "book": {
                                "id": 1,
                                "title": "Sample Book",
                                "author": "Author",
                                "cover": "HARD",
                                "inventory": 1,
                                "daily_fee": 1.50,
                            },
                            "user_email": "user@example.com",
                            "borrow_date": "2023-01-01",
                            "expected_return_date": "2023-01-08",
                            "actual_return_date": None,
                            "is_active": True
                        }
                    )
                ]
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


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
