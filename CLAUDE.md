# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered QA Test Case Generator - a full-stack platform that automatically generates test cases from requirements using LLMs. It consists of a FastAPI backend (`app/`) and a React/TypeScript frontend (`web/`).

## Development Commands

### Backend

```bash
# Start backend server (handles dependency checks: Redis, Qdrant, PostgreSQL)
./start-backend.sh

# Stop backend server
./stop-backend.sh

# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Run single test file
pytest tests/test_specific_file.py

# Run specific test
pytest tests/test_specific_file.py::test_function_name
```

### Frontend

```bash
cd web

# Development server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

### Services (via Docker)

```bash
# Start all services (PostgreSQL, Redis, Qdrant)
docker-compose up -d

# Start individual services
docker start qa-orchestrator-redis
docker start qa-orchestrator-db
docker start qdrant
```

## Architecture

### Backend Pipeline (`app/pipeline/`)

The core test case generation is a **multi-stage pipeline**:

1. **Preprocessor** - Cleans and normalizes input requirements
2. **Prompt Builder** - Constructs specialized prompts for different test types (functional, negative, boundary)
3. **LLM Router** - Routes to appropriate LLM provider (Ollama, OpenAI, or GLM)
4. **Postprocessor/Parser** - Parses LLM outputs with robust JSON extraction
5. **Validator** - Validates test case structure and completeness
6. **Analyzer** - Computes coverage metrics and risk assessment

Key entry point: `app/pipeline/orchestrator.py` contains the `orchestrate()` function.

### LLM Integration (`app/pipeline/llm/`)

- **LLM Router** (`llm_router.py`): Abstracts different LLM providers
- **Ollama Client**: Default for local models (Llama 3.1, etc.)
- **OpenAI Client**: Fallback for cloud models
- **GLM Client**: New provider (in development)

### RAG System (`app/api/v1/rag/`)

Advanced Retrieval-Augmented Generation for document-based test generation:
- Semantic re-ranking with cross-encoder models
- Query expansion for better recall
- Hybrid search (semantic + keyword via Reciprocal Rank Fusion)
- Full citation tracking

See `ADVANCED_RAG_GUIDE.md` for detailed RAG documentation.

### Database

- **PostgreSQL** via SQLAlchemy 2.0 with async support
- **Alembic** for migrations (`alembic/` directory)
- Connection pooling configured in `app/core/config.py`

### State Management

- **Redis**: Caching and queue management
- **Qdrant**: Vector database for document embeddings

### Frontend Architecture (`web/`)

- **React 19** with TypeScript and Vite
- **Zustand** for state management (see `web/src/store/`)
- **React Router v7** for routing
- **Radix UI** primitives with Tailwind CSS styling
- API client communicates with backend at `http://localhost:8000`

## Configuration

All settings are in `app/core/config.py` using Pydantic Settings. Environment variables are loaded from `.env`:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `OLLAMA_URL`: Local Ollama server (default: `http://localhost:11434`)
- `OPENAI_API_KEY`: Optional OpenAI API key
- `QDRANT_HOST`/`QDRANT_PORT`: Vector database connection
- `REDIS_HOST`/`REDIS_PORT`: Cache connection

## API Structure (`app/api/v1/`)

- `/v1/auth` - Registration, login, JWT refresh
- `/v1/orchestrator` - Test case generation (main pipeline)
- `/v1/documents` - Document upload and processing for RAG
- `/v1/rag` - Advanced RAG operations
- `/v1/test-cases` - Test case CRUD
- `/v1/requirements` - Requirements library
- `/v1/history` - Session history
- `/v1/analytics` - Usage statistics
- `/v1/dashboard` - Dashboard data

## Testing

Tests use `pytest` with `pytest-asyncio` for async test support. Test files are in `tests/` matching the `app/` directory structure.

## Important Notes

- The backend requires **Ollama** running for local LLM inference, or an OpenAI API key
- **Qdrant** must be running for RAG/document features
- **PostgreSQL** and **Redis** are required for full functionality
- The orchestrator has multiple versions (V6, V7) - V6 in `orchestrator.py` is the current stable version
- When adding new LLM providers, register them in `llm_router.py` and create a client in `app/pipeline/llm/`
