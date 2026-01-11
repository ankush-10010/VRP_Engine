@echo off
echo Starting FastAPI Server (Hot Reload Enabled)...
echo Make sure you have your .env file set up!
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
