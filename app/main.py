from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .api import endpoints

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Hybrid Delivery Optimization API",
    description="API for route optimization using OR-Tools and Google Maps",
    version="1.0.0"
)

# CORS
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://vrp-engine.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Optimization API is running. Go to /docs for Swagger UI."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
