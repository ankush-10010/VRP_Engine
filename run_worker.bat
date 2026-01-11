@echo off
echo Starting Celery Worker (Windows Mode)...
echo Make sure you have Redis running (docker run -p 6379:6379 redis:alpine)
echo Make sure you have your .env file set up!
celery -A app.worker.celery_app worker --pool=solo --loglevel=info
