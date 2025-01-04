# Create your views here.
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from authentication.middleware import User
from authentication.serializers import UserDetailSerializer, UserSerializer, AvatarUpdateSerializer


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


class UserViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = User.objects.filter(is_superuser=False).all()

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering = ['-score']
    ordering_fields = ['score', 'username']

    def get_queryset(self):
        queryset = super().get_queryset()

        ordering_param = self.request.query_params.get('ordering', None)

        if ordering_param:
            valid_ordering_fields = ['score', 'username']
            if ordering_param not in valid_ordering_fields:
                raise ValidationError("Invalid ordering field")
            queryset = queryset.order_by(ordering_param)

        return queryset


class UserDetailViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserDetailSerializer
    pagination_class = LimitOffsetPagination

    @action(detail=False, methods=['get'], url_path=r'(?P<username>[^/]+)')
    def profile(self, request, username=None):
        user = get_object_or_404(User, username=username)
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class UserInfoViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = AvatarUpdateSerializer
    parser_classes = [FormParser, MultiPartParser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'avatar', openapi.IN_FORM, description="User avatar", type=openapi.TYPE_FILE
            )
        ]
    )
    @action(detail=False, methods=['post'], url_path='avatar')
    def avatar(self, request):
        user = request.user
        serializer = AvatarUpdateSerializer(instance=user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Avatar updated successfully.", "data": serializer.data},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteUserView(viewsets.GenericViewSet, mixins.DestroyModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
