import uuid

from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

User = get_user_model()


class Leaderboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    score = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "leaderboard"
