import os
import uuid
from uuid import UUID

from django.core.files.base import ContentFile
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from zipp.compat.overlay import zipfile

from question.models import Question
from topic.models import Topic
from topic.serializers import TopicSerializer


# Create your views here.


class TopicViewSet(ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def get_object(self):
        obj = get_object_or_404(Topic, id=self.kwargs['pk'])
        return obj

    def get_queryset(self):
        category = self.request.query_params.get('category', None)
        if category == 'user':
            queryset = Topic.objects.filter(owner=self.request.user).all()
        else:
            queryset = Topic.objects.filter(owner__isnull=True).all()
        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='category',
                in_=openapi.IN_QUERY,
                description="Filter by category",
                type=openapi.TYPE_STRING,
                enum=['user', 'system']
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            request.data['owner'] = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            obj = self.get_object()
            if obj.owner != request.user:
                return Response("PERMISSION DENIED", status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class TopicImportView(GenericViewSet):
    queryset = Topic.objects.all()
    serializer_class = None
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'file', openapi.IN_FORM, type=openapi.TYPE_FILE, description="File zip chứa ảnh"
        ),
        openapi.Parameter(
            'name', openapi.IN_FORM, type=openapi.TYPE_STRING, description="name của Topic"
        )
    ],
        responses={201: "Created"})
    @action(detail=False, methods=['POST'], name='upload')
    def import_topics(self, request, *args, **kwargs):

        file = request.FILES.get('file')
        name = request.data.get('name')

        if not file or not name:
            return Response({"error": "File zip và topic_id là bắt buộc."}, status=status.HTTP_400_BAD_REQUEST)
            # Lấy đối tượng Topic

        try:
            with zipfile.ZipFile(file, 'r') as zip_file:

                images = [f for f in zip_file.namelist() if f.lower().endswith(('png', 'jpg', 'jpeg', "jfif",))]
                questions = []

                if request.user.is_superuser:
                    topic = Topic(name=name, is_published=True)
                else:
                    topic = Topic(name=name, is_published=True, owner=request.user)

                banner = 'banner'
                for ex_file in ('png', 'jpg', 'jpeg', "jfif"):
                    if f'{banner}.{ex_file}' in images:
                        banner = f'{banner}.{ex_file}'
                        break
                banner_data = zip_file.read(banner)
                topic.banner.save(banner, ContentFile(banner_data), save=False)
                topic.save()

                for image_name in images:
                    if image_name == banner:
                        continue
                    # Đọc nội dung file ảnh
                    image_data = zip_file.read(image_name)
                    # Tạo đối tượng Question
                    question = Question(
                        answer_text=os.path.splitext(os.path.basename(image_name))[0],
                        topic=topic
                    )
                    # Lưu file ảnh vào đối tượng
                    question.image.save(image_name, ContentFile(image_data), save=False)
                    questions.append(question)
                # Bulk create các Question
                Question.objects.bulk_create(questions)

            return Response({"message": f"Tạo thành công {len(questions)} câu hỏi."}, status=status.HTTP_201_CREATED)

        except zipfile.BadZipFile:
            return Response({"error": "File không phải định dạng zip hoặc bị lỗi."}, status=status.HTTP_400_BAD_REQUEST)
