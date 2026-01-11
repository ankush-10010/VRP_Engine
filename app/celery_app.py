from celery import Celery
import os

# Get Redis URL from env or default to localhost
# In Docker, the hostname 'redis' is used (defined in docker-compose)
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "optimization_worker",
    broker=BROKER_URL,
    backend=RESULT_BACKEND
)



