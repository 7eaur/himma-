import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from protected import router as protected_router
from assessment import router as assessment_router
from temporary_audio_skip import router as temporary_audio_skip_router
from review import router as review_router
from recordings import router as recordings_router
from activities import router as activities_router
from adaptation import router as adaptation_router
from adaptation_runtime import router as adaptation_runtime_router
from reinforcement_review import router as reinforcement_review_router
from media import router as media_router
from speech_analysis import router as speech_analysis_router
from journey import router as journey_router

app = FastAPI(
    title="Himma API Service",
    description="API service for Himma Educational Platform",
    version="0.1.0",
)

# CORS — allows the Next.js dev server and production URL
_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(protected_router)
app.include_router(journey_router)
# TEMPORARY: this router must precede assessment_router so its finish endpoint
# can apply a neutral denominator only when explicit audio-skip markers exist.
app.include_router(temporary_audio_skip_router)
app.include_router(assessment_router)
app.include_router(activities_router)
app.include_router(adaptation_router)
app.include_router(adaptation_runtime_router)
app.include_router(reinforcement_review_router)
app.include_router(media_router)
app.include_router(review_router)
app.include_router(recordings_router)
app.include_router(speech_analysis_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "himma-api"}
