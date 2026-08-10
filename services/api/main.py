import os
# Set test secret BEFORE any other imports so dependencies.py picks it up
os.environ["API_SECRET_KEY"] = "test-secret-key-for-ci-only"

from fastapi import FastAPI
from auth import router as auth_router
from protected import router as protected_router

app = FastAPI(
    title="Himma API Service",
    description="API service for Himma Educational Platform",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(protected_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "himma-api"}
