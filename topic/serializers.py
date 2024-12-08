from rest_framework import serializers

from topic.models import Topic


class TopicSerializer(serializers.ModelSerializer):
    banner = serializers.ImageField(use_url=True)
    owner = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    count_image = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ['id', 'banner', 'name', 'owner', 'count_image']

    def get_count_image(self, obj):
        return obj.questions.count()
