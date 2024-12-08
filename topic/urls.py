# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from topic.views import TopicViewSet, TopicImportView

# Router cho ViewSet
router = DefaultRouter()
router.register('topic', TopicImportView, basename='topic')
router.register('topic', TopicViewSet, basename='topic')

urlpatterns = router.urls
