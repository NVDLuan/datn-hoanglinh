from django.urls import path, include
from rest_framework.routers import DefaultRouter

from authentication.views import GoogleLogin, FacebookLogin, UserViewSet, UserDetailViewSet, UserInfoViewSet, \
    DeleteUserView

router = DefaultRouter()
router.register('users', UserInfoViewSet, basename='users')
router.register('users', DeleteUserView, basename='users')
router.register('users', UserViewSet, basename='users')
router.register('users', UserDetailViewSet, basename='users')

urlpatterns = [
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/google/', GoogleLogin.as_view()),
    path('auth/facebook/', FacebookLogin.as_view()),

    path('', include(router.urls)),

]
