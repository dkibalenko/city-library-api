from django.urls import path

from borrowings import views

app_name = "borrowings"

urlpatterns = [
    path("", views.BorrowingList.as_view(), name="borrowings"),
    path(
        "<int:pk>/",
        views.BorrowingDetail.as_view(),
        name="borrowing-detail",
    ),
]
