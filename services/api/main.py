from fastapi import FastAPI
from auth import router as auth_router

app = FastAPI(
    title="Himma API Service",
    description="API service for Himma Educational Platform",
    version="0.1.0",
)

app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "himma-api"}
