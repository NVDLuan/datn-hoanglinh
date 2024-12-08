# Create your views here.
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import viewsets, permissions, mixins
from rest_framework.pagination import LimitOffsetPagination

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

