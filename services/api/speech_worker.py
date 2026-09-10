"""P07 speech worker entrypoint.

Usage:
    python speech_worker.py --once
    python speech_worker.py --poll-seconds 3

The worker discovers uploaded audio that has no queue row, atomically leases one
due job at a time, commits that lease before any provider call, then processes
only jobs owned by this worker. A crash leaves a durable lease that can be
reclaimed after expiry; it never fabricates ASR results when no provider is
approved/configured.
"""

from __future__ import annotations

import argparse
import os
import socket
import time
import uuid

from db.database import SessionLocal
from db.models import AudioSubmission
from db.speech_models import SpeechAnalysisJob
from speech_pipeline import claim_next_job, enqueue_submission, process_job


def discover_jobs(db, limit: int = 100) -> int:
    existing = db.query(SpeechAnalysisJob.submission_id)
    submission_ids = [
        row.id
        for row in db.query(AudioSubmission.id).filter(
            AudioSubmission.status == "uploaded",
            ~AudioSubmission.id.in_(existing),
        ).order_by(AudioSubmission.submitted_at, AudioSubmission.id).limit(limit).all()
    ]
    for submission_id in submission_ids:
        enqueue_submission(db, submission_id)
    if submission_ids:
        db.commit()
    return len(submission_ids)


def _worker_id() -> str:
    explicit = os.getenv("HIMMA_ASR_WORKER_ID", "").strip()
    if explicit:
        return explicit[:160]
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex}"[:160]


def run_cycle(limit: int = 10, *, worker_id: str | None = None) -> dict[str, int]:
    db = SessionLocal()
    discovered = processed = blocked = 0
    owner = worker_id or _worker_id()
    try:
        discovered = discover_jobs(db)
        for _ in range(limit):
            job = claim_next_job(db, worker_id=owner)
            if job is None:
                db.rollback()
                break
            job_id = job.id
            # Claim must be visible before the external provider call so another
            # worker sees the durable processing lease and SKIP LOCKED behavior.
            db.commit()
            job = process_job(db, job_id, worker_id=owner)
            db.commit()
            processed += 1
            if job.status == "blocked_provider":
                blocked += 1
        return {"discovered": discovered, "processed": processed, "blocked_provider": blocked}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Himma speech analysis worker")
    parser.add_argument("--once", action="store_true", help="Run one queue cycle and exit")
    parser.add_argument("--poll-seconds", type=float, default=float(os.getenv("HIMMA_ASR_POLL_SECONDS", "3")))
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    if args.poll_seconds < 0.5:
        parser.error("--poll-seconds must be at least 0.5")
    if args.limit < 1 or args.limit > 100:
        parser.error("--limit must be between 1 and 100")

    worker_id = _worker_id()
    while True:
        print(run_cycle(limit=args.limit, worker_id=worker_id), flush=True)
        if args.once:
            return
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
