# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from play_game.views import RoomView

# Router cho ViewSet
router = DefaultRouter()
router.register('room', RoomView, basename='room')

urlpatterns = router.urls