# RESUME HERE — P02 Baseline Recovery

**Last updated:** 2026-08-18T22:42:00Z  
**Branch:** `recovery/p02-baseline`  
**HEAD:** `616a2ac`

## Current Status: LOCAL STACK VERIFIED ✓

All 12 integration checks passed at `2026-08-18T22:41:46`:

| Check | Result |
|---|---|
| FastAPI /health | ✓ ok |
| Researcher login | ✓ 200 + JWT cookie |
| /me endpoint | ✓ role=researcher |
| Create student | ✓ id + access_code |
| Admin logout | ✓ 200 |
| Student login | ✓ 200 + JWT cookie |
| Student profile | ✓ 200 |
| Start assessment | ✓ session_id created in PostgreSQL |
| Get question | ✓ id=1, type=multiple_choice (real Arabic content) |
| Submit answer | ✓ saved to PostgreSQL attempts table |
| Upload audio | ✓ 25005 bytes in MinIO himma-audio bucket |
| Verify in DB | ✓ 1 attempt, 1 session row in PostgreSQL |

## Local Services

| Service | URL | Status |
|---|---|---|
| PostgreSQL 18 | `localhost:5432` | Windows Service (auto) |
| MinIO | `http://localhost:9000` | Manual terminal |
| Redis | `localhost:6379` | Manual terminal |
| FastAPI | `http://localhost:8000` | Manual terminal |
| Next.js | `http://localhost:3000` | Not started yet |

## How to Start Services

1. **PostgreSQL** — runs automatically as Windows service
2. **MinIO** — open CMD, run:
   ```cmd
   set MINIO_ROOT_USER=<set-locally>
   set MINIO_ROOT_PASSWORD=<set-locally>
   C:\himma-services\minio\minio.exe server E:\himma-services\minio-data --console-address :9001 --address :9000
   ```
3. **Redis** — open CMD, run:
   ```cmd
   C:\himma-services\redis\redis-server.exe
   ```
4. **FastAPI** — open CMD, run:
   ```cmd
   set DATABASE_URL=<set-locally>
   set API_SECRET_KEY=<set-locally>
   set S3_ENDPOINT=http://localhost:9000
   set S3_ACCESS_KEY=<set-locally>
   set S3_SECRET_KEY=<set-locally>
   set S3_BUCKET_NAME=himma-audio
   set REDIS_URL=redis://localhost:6379/0
   set ENV=development
   cd /d "e:\مشروع منصه همه\Himma_Unified_Repository_v1.1_FINAL\services\api"
   python run_dev.py
   ```
5. **Next.js** — open CMD, run:
   ```cmd
   cd /d "e:\مشروع منصه همه\Himma_Unified_Repository_v1.1_FINAL\apps\web"
   set NEXT_PUBLIC_API_URL=http://localhost:8000
   npm run dev
   ```

## Local credentials

لا تُحفظ قيم الاتصال في المستودع. أنشئ قيمًا محلية جديدة في `.env` غير
المرفوع، ودوّر القيم التي كانت موثقة سابقًا قبل إعادة استخدامها.

## Next Step: P02 Slice 2 — Next.js + End-to-End Browser Flow
- Start Next.js dev server
- Fix admin login UI (no redirect loop)  
- Verify full browser flow: login → create student → student session → audio recording
- Fix any remaining middleware redirect issues
