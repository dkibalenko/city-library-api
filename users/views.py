from django.contrib.auth import get_user_model

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

from users.serializers import UserSerializer


class CreateUserView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [AllowAny]
        elif self.request.method == "GET":
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()
