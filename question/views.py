from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from question.models import Question
from question.serializers import QuestionSerializer


# Create your views here.


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def get_queryset(self):
        topic_id = self.request.query_params.get('topic', None)
        if topic_id:
            return Question.objects.filter(topic_id=topic_id)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='topic',
                in_=openapi.IN_QUERY,
                description="topic of the question",
                type=openapi.TYPE_STRING
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
