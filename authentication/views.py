# Create your views here.
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from authentication.middleware import User
from authentication.serializers import UserDetailSerializer, UserSerializer


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


class UserViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination


class UserDetailViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserDetailSerializer
    pagination_class = LimitOffsetPagination

    @action(detail=False, methods=['get'], url_path=r'(?P<username>[^/]+)')
    def profile(self, request, username=None):
        # Fetch the user by username
        user = get_object_or_404(User, username=username)
        # Serialize the user data
        serializer = self.get_serializer(user)
        return Response(serializer.data)
