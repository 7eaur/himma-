from fastapi import FastAPI

app = FastAPI(
    title="Himma API Service",
    description="API service for Himma Educational Platform",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "himma-api"}
