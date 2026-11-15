# Frontend

The frontend is a React 19 single-page dashboard built with Vite. It submits evaluations to the FastAPI backend and displays evaluation results, analytics, and paginated history.

## Requirements

- Node.js `^20.19.0` or `>=22.12.0` and npm
- The backend running at `http://127.0.0.1:8000` (the API address is currently defined directly in `src/App.jsx`)

## Install and run

From this directory:

```bash
npm ci
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`. The app loads analytics and evaluation history on startup. Submit a prompt and response; adding a reference answer also requests deterministic and Ollama LLM judging. Use the history controls to page through saved results or open an evaluation again.

## Scripts

- `npm run dev` starts the Vite development server.
- `npm run build` creates a production bundle in `dist/`.
- `npm run preview` serves the existing production bundle locally.
- `npm run lint` runs Oxlint.

The frontend does not currently define an environment variable for the backend URL. The backend's CORS middleware permits cross-origin requests, and its API must be started separately. See the [project README](../README.md) for backend setup, API routes, and test instructions.
