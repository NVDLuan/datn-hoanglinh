from celery import shared_task

from topic.models import Topic


@shared_task
def process_record_task(record_id):
    try:
        # Lấy record từ database
        record = Topic.objects.get(id=record_id)
        # Thực hiện xử lý logic
        print(f"Processing record with ID: {record_id}")
        # Ví dụ: Update trạng thái hoặc gửi thông báo

    except Topic.DoesNotExist:
        print(f"Record with ID {record_id} not found.")
