# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from topic.models import Topic
from topic.task import process_record_task


@receiver(post_save, sender=Topic)
def handle_post_save(sender, instance, created, **kwargs):
    if created:
        process_record_task.delay(instance.id)