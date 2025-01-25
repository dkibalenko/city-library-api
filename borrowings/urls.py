from django.urls import path

from borrowings import views

app_name = "borrowings"

urlpatterns = [
    path("", views.BorrowingListView.as_view(), name="borrowings"),
    path(
        "<int:pk>/",
        views.BorrowingDetailView.as_view(),
        name="borrowing-detail",
    ),
]
