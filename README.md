# AI Evaluation Platform

A production-oriented platform for evaluating and benchmarking LLM applications.

## Overview

The AI Evaluation Platform evaluates AI-generated responses using deterministic evaluation and an LLM-based judge.

The platform provides:

- Deterministic response evaluation
- LLM-based evaluation using Ollama
- Evaluation comparison
- Persistent SQLite evaluation history
- Evaluation history pagination
- Evaluation analytics
- Structured API error handling
- React evaluation dashboard
- Automated backend test coverage

## Technology Stack

### Backend

- Python 3.13+
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- SQLite
- Ollama

### Frontend

- React 19
- Vite 8
- JavaScript
- CSS

### Testing

- pytest
- FastAPI TestClient
- httpx

## Architecture

```text
React Frontend
      |
      | HTTP
      v
FastAPI Backend
      |
      +----------------------+
      |                      |
      v                      v
Deterministic Evaluator   Ollama LLM Judge
      |                      |
      +----------+-----------+
                 |
                 v
          Comparison Layer
                 |
                 v
          SQLite Persistence
                 |
                 v
          Evaluation History
                 |
                 v
              Analytics