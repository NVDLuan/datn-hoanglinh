# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from question.views import QuestionViewSet

# Router cho ViewSet
router = DefaultRouter()
router.register("", QuestionViewSet , basename='question')

# URL patterns
urlpatterns = [
    path(r'question/', include(router.urls)),
]