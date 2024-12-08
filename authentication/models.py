import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


# Create your models here.



class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    class Meta:
        db_table = "user"

