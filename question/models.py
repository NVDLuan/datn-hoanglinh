import os
import uuid

from django.db import models

from topic.models import Topic


# Create your models here.
def get_image_upload_to(instance, filename):
    topic_id = instance.topic.id if instance.topic else 'default'
    return os.path.join("question_images", str(topic_id), filename)


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to=get_image_upload_to, null=True, blank=True)
    answer_text = models.CharField(max_length=600)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="questions", related_query_name="question")

    class Meta:
        db_table = 'question'
