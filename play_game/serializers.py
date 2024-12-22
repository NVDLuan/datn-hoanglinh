from rest_framework import serializers


class RoomSerializer(serializers.Serializer):
    topics = serializers.ListField(child=serializers.UUIDField())
    type = serializers.ChoiceField(
        choices=['fighting', 'examiner'],
        default='fighting'
    )
    time = serializers.IntegerField(default=0)


class CreatedBySerializer(serializers.Serializer):
    username = serializers.CharField()  # Tên người dùng
    avatar = serializers.URLField(allow_null=True, required=False)  # URL avatar, có thể null


class RoomResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    time = serializers.IntegerField(default=0)
    topics = serializers.ListField(child=serializers.CharField(), default=[])  # Danh sách topics
    created_by = CreatedBySerializer()  # Thông tin người tạo
