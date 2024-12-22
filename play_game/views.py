import json
import uuid

import redis
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from play_game.serializers import RoomSerializer, RoomResponseSerializer


# Create your views here.


class RoomView(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'create':
            return RoomSerializer
        elif self.action == 'list':
            return RoomResponseSerializer
        else:
            return RoomResponseSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user  # Lấy thông tin user từ request

        # Kết nối với Redis
        redis_client = redis.StrictRedis.from_url(settings.REDIS_URL)

        # Tạo ID ngẫu nhiên
        room_id = str(uuid.uuid4())[-12:]

        # Thêm thông tin user tạo phòng
        room_data = {
            "id": room_id,
            'topics': data.get('topics', []),
            'time': data.get('time', 60),
            "type": data.get('type', ""),
            "created_by": {
                "username": user.username,
                "avatar": user.profile.avatar.url if hasattr(user, "profile") else None,  # Avatar nếu có
            }
        }

        # Lưu dữ liệu vào Redis
        room_key = f"room_game:{room_id}"  # Tạo khóa duy nhất cho phòng
        redis_client.set(room_key, json.dumps(room_data))

        return Response({"id": room_id, "message": "Room created successfully!"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('search', in_=openapi.IN_QUERY, description="search id room", type=openapi.TYPE_STRING)])
    def list(self, request, *args, **kwargs):
        redis_client = redis.StrictRedis.from_url(settings.REDIS_URL)
        search = request.query_params.get('search', None)
        if search:
            keys = redis_client.keys(f"room_game:{search}*")
        else:
            # Lấy tất cả các khóa liên quan đến rooms
            keys = redis_client.keys("room_game:*")

        # Danh sách chứa thông tin các phòng
        rooms = []

        for key in keys:
            room_data = redis_client.get(key)  # Lấy dữ liệu JSON từ Redis
            if room_data:
                rooms.append(json.loads(room_data))  # Parse JSON thành dict

        # Trả về danh sách các phòng
        return Response(rooms, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        redis_client = redis.StrictRedis.from_url(settings.REDIS_URL)

        room_data = redis_client.get(f"room_game:{kwargs['pk']}")
        if room_data:
            return Response(json.loads(room_data), status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(methods=['delete'], detail=False)
    def delete_redis(self, request, *args, **kwargs):
        redis_client = redis.StrictRedis.from_url(settings.REDIS_URL)
        pattern = "room:*:players"
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
            print(f"Deleted key: {key}")
        return Response(status=status.HTTP_200_OK)
