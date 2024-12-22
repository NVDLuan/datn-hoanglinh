# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from leaderboard.views import LeaderboardViewSet

# Router cho ViewSet
router = DefaultRouter()
router.register("", LeaderboardViewSet , basename='leaderboard')

# URL patterns
urlpatterns = [
    path(r'leaderboard/', include(router.urls)),
]