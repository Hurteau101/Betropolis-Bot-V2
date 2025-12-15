from datetime import timedelta
from celery import Celery
from runner import EsportsRunner
import redis

celery_app = Celery(
    "notify_user_celery",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

celery_app.conf.beat_schedule = {
    "send_notifications": {
        "task": "notification.notify_user",
        "schedule": timedelta(seconds=45),
    },
}

@celery_app.task(name="notification.notify_user", time_limit=90, soft_time_limit=75)
def notify_user():
    r = redis.Redis(host="localhost", port=6379, db=0)

    lock = r.lock("notify_user_lock", timeout=120, blocking=False)
    if not lock.acquire():
        return

    try:
        runner = EsportsRunner()
        runner.run_bot()
    finally:
        lock.release()



# celery -A notification worker --loglevel=info --pool=solo
# celery -A notification beat --loglevel=info
