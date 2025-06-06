# Import tasks to register them with the Celery app
import scheduler.tasks
from scheduler.celery_app import celery_app

# This ensures that the tasks are registered with the Celery app
__all__ = ["celery_app"]
