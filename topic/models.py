import uuid

from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
User = get_user_model()


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    banner = models.ImageField(null=True, blank=True, upload_to="banners/")
    is_published = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "topic"
