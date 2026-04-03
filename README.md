# PDF Summary AI

Take-home demo: upload a PDF, extract text with PyMuPDF, summarize through OpenRouter (OpenAI-compatible API), and inspect the last five uploads in a small React UI.

## Stack

| Layer | Choices |
|--------|---------|
| API | FastAPI, Pydantic, `BackgroundTasks` |
| Data | SQLAlchemy, SQLite |
| PDF | PyMuPDF |
| LLM | `openai` SDK → OpenRouter |
| UI | React 18, TypeScript, Vite |
| Deploy locally | Docker Compose |

## Architecture

Uploads are stored as `{id}.pdf` on disk; metadata lives in SQLite. The API returns immediately with `status=uploaded`. One background job per document moves `uploaded` → `processing` → `done` or `failed`: extract text by page, chunk (~7k chars, paragraph-aware), summarize each chunk, merge chunk summaries in a second call. The browser polls `GET /api/documents/{id}` until the job finishes. No queue, no Redis, no websocket.

## Docker

1. Copy `.env.example` to `.env` and set your OpenRouter key (never commit `.env`).
2. From the repo root:

```bash
docker compose up --build
```

- App: http://localhost:5173  
- API: http://localhost:8000  
- OpenAPI: http://localhost:8000/docs  

Data and uploads use Compose volumes (`backend_data`, `backend_uploads`). Secrets are loaded into the backend via `env_file: .env`, not hardcoded in `docker-compose.yml`.

## Local development

**Backend** (Python 3.12+):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# export OPENROUTER_API_KEY=...  (and optional OPENROUTER_* vars)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev
```

Point the UI at the API with `VITE_API_URL` if needed (default `http://localhost:8000`). **Do not** put API keys in any `VITE_*` variable.

## Environment variables

| Variable | Role |
|----------|------|
| `OPENROUTER_API_KEY` | Required for uploads; server-side only. |
| `OPENROUTER_MODEL` | OpenRouter model id (default in `.env.example`). |
| `OPENROUTER_BASE_URL` | Usually `https://openrouter.ai/api/v1`. |
| `OPENROUTER_APP_NAME` | Optional; sent as `X-Title`. |
| `OPENROUTER_SITE_URL` | Optional; sent as `HTTP-Referer`. |
| `DATABASE_URL` | SQLAlchemy URL (SQLite default in example). |
| `UPLOAD_DIR` | Directory for PDF files. |
| `MAX_UPLOAD_MB` | Upload size cap. |
| `MAX_TOTAL_CHARS` | Max extracted characters before summarization (default 350000; avoids huge LLM runs). |
| `CORS_ORIGINS` | Browser origins allowed by the API. |
| `VITE_API_URL` | Frontend-only API base URL. |

If `OPENROUTER_API_KEY` is missing, `POST /api/documents` returns **503** before anything is written to the database or disk.

## API

| Method | Path | Notes |
|--------|------|--------|
| `POST` | `/api/documents` | Multipart field `file`. PDF only. |
| `GET` | `/api/documents` | Latest 5 rows, newest first. |
| `GET` | `/api/documents/{id}` | Single row; poll while `uploaded` or `processing`. |

Errors use `{"detail": ...}` (string or object with `message` / `error`).

## Limitations

- **Text-layer PDFs only.** No OCR; scans or image-only pages usually fail or produce useless text.
- **Processing is in-process.** Restarting the API can strand a row in `uploaded` or `processing`.
- **Cost / latency** scale with pages and chunks (one LLM call per chunk plus a merge). Extracted text over **`MAX_TOTAL_CHARS`** (default 350k) fails fast with a clear message so demos do not run away on enormous text-heavy PDFs. Even under that limit, long text-heavy PDFs can still take **several minutes** before the UI shows **Done**—that is expected.

## Demo (quick)

1. Start stack (Docker or local uvicorn + `npm run dev`).
2. Open the UI, upload a **digital** PDF (exported from Word/Google Docs, or a text-heavy paper with a real text layer).
3. Watch the selected document go from Uploaded → Processing → Done; summary appears when ready.
4. Open **Recent uploads** to compare statuses; click another row to inspect it.

**Best PDFs:** native digital text, not camera scans.  
**Out of scope on purpose:** auth, multi-user isolation, durable job queues, OCR, RAG/vectors, real-time push.

## Possible improvements

- Alembic migrations and explicit schema versioning.
- Retry or dead-letter handling for stuck `processing` rows.
- Pagination or search if the list grows beyond five.
- Rate limits and upload quotas for a public deployment.
