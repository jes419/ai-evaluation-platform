# AI Evaluation Platform

A FastAPI service and React dashboard for comparing deterministic response scores with an Ollama LLM judge. Evaluation history and analytics are stored in a local SQLite database.

## Prerequisites

- Python 3.13 or newer and [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- [Ollama](https://ollama.com/) with the `qwen3:8b` model available for evaluations that include a reference answer

Pull the model before using LLM judging:

```bash
ollama pull qwen3:8b
```

Keep Ollama running while making judged evaluations. Requests without a reference answer are saved without deterministic scores or an LLM judge result.

## Run locally

### Backend

From the repository root, install the project and development dependencies, then start the API:

```bash
uv sync --dev
uv run uvicorn main:app --reload
```

The API listens at `http://127.0.0.1:8000`. Its interactive OpenAPI documentation is at `http://127.0.0.1:8000/docs`. SQLite data is stored in `evaluation.db` in the current working directory. The application does not define environment-variable configuration.

### Frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). The dashboard calls the API at `http://127.0.0.1:8000`; start the backend first.

To create a production frontend build:

```bash
cd frontend
npm run build
```

Vite writes the build output to `frontend/dist`.

## Use the dashboard

Enter a prompt and AI response. Add a reference answer to run deterministic evaluation, LLM judging, and comparison; without it, the request is saved without scores. The dashboard displays the result, aggregate analytics, and saved history. Use **View** to reload an item, **Previous** and **Next** to page through history, and **Refresh** to reload analytics or history.

## API

All routes are served by the backend at `http://127.0.0.1:8000`:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Health-style message confirming the service is running. |
| `POST` | `/evaluate` | Evaluate and save a request. JSON requires nonblank `prompt` and `response`; optional nonblank `reference_answer` enables scoring and LLM judging. |
| `GET` | `/evaluations?limit=10&offset=0` | Return a page of saved evaluations and pagination metadata. `limit` must be 1–100; `offset` must be nonnegative. |
| `GET` | `/evaluations/{evaluation_id}` | Retrieve one evaluation by its UUID. |
| `GET` | `/analytics` | Return aggregate counts, pass rate, average deterministic and LLM scores, and comparison differences. |

For example, submit an evaluation with `curl`:

```bash
curl -X POST http://127.0.0.1:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is Python?","response":"Python is a programming language.","reference_answer":"Python is a programming language."}'
```

Validation errors return HTTP 422. If Ollama is unavailable, a judged evaluation returns HTTP 503; an invalid judge response returns HTTP 502. FastAPI's `/docs` page provides request and response schemas.

## Tests

Run the backend test suite from the repository root:

```bash
uv run pytest
```

## Frontend documentation

See [`frontend/README.md`](frontend/README.md) for frontend-specific setup, scripts, and dashboard/API connection details.
