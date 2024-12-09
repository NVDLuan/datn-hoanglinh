"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi

from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="DO AN TOT NGHIEP",
        default_version='v1', ),
    public=True,
    permission_classes=[permissions.AllowAny],
)
urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/', include('authentication.urls')),
                  path('api/', include('topic.urls')),
                  path('api/', include('question.urls')),
                  path('api/', include('leaderboard.urls')),
                  path('api/', include('play_game.urls')),

                  path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
              ] + static("media", document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL,
                                                                              document_root=settings.STATIC_ROOT) + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)