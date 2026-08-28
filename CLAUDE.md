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
3. **LLM Router** - Routes to appropriate LLM provider (Ollama, GLM, Groq, Gemini)
4. **Postprocessor/Parser** - Parses LLM outputs with robust JSON extraction
5. **Validator** - Validates test case structure and completeness
6. **Analyzer** - Computes coverage metrics and risk assessment

Key entry point: `app/pipeline/orchestrator.py` contains the `orchestrate()` function.

### LLM Integration (`app/pipeline/llm/`)

The **Multi-LLM Router** (`multi_llm_router.py`) supports multiple providers and strategies:

**Providers:**
- **Ollama** (`client_ollama.py`): Local models (llama3.1, mistral, phi, etc.)
- **GLM** (`glm_client.py`): Z.AI GLM API (glm-4-plus, glm-4-flash) - has strict rate limiting
- **Groq** (`groq_client.py`): Fast cloud inference (llama-3.1-8b, mixtral)
- **Gemini** (`gemini_client.py`): Google Gemini 2.0 Flash (generous free tier)

**Strategies:**
- **SINGLE**: Use primary model only
- **ENSEMBLE**: Run multiple models and merge results (weighted, majority, concat)
- **CASCADE**: Try primary, fallback to secondary on failure

**GLM Rate Limiting**: The GLM API has very strict concurrency limits (error 1302). All GLM requests go through a queue-based rate limiter (`rate_limited_glm_generate`) that processes them sequentially with a 3-second delay between requests.

**Configuration Schema** (`app/schemas/llm_schema.py`):
- Simple modes: `local_only`, `glm_only`, `combined`
- Advanced: Custom strategy with primary/secondary models, weights, merge methods
- Per-type model overrides for different test types (functional, negative, boundary)

### Orchestrator Versions

Multiple orchestrator versions exist for different use cases:

- **`orchestrator.py` (V6)**: Current stable version - clean summary + stable TC generation
- **`orchestrator_v7.py` (V7)**: Supports multi-LLM configurations, parallel summary/space generation
- **`orchestrator_v72.py` (V7.2)**: Enhanced test space analysis with intent-based generation

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

The main orchestrator store (`web/src/store/orchestrator.store.ts`) manages:
- Provider selection: `local`, `groq`, `gemini`
- Advanced RAG options: `useRAG`, `useAdvancedRAG`, `useQueryExpansion`, `useReranking`
- Model selection, boundary generation, risk assessment

## Configuration

All settings are in `app/core/config.py` using Pydantic Settings. Environment variables are loaded from `.env`:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `OLLAMA_URL`: Local Ollama server (default: `http://localhost:11434`)
- `GLM_API_KEY`: Z.AI GLM API key
- `GROQ_API_KEY`: Groq API key
- `GEMINI_API_KEY`: Google Gemini API key (get at https://aistudio.google.com/apikey)
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

## Important Notes

- The backend requires **Ollama** running for local LLM inference, or API keys for cloud providers
- **Qdrant** must be running for RAG/document features
- **PostgreSQL** and **Redis** are required for full functionality
- When adding new LLM providers:
  1. Add provider to `LLMProvider` enum in `app/schemas/llm_schema.py`
  2. Create client in `app/pipeline/llm/` following existing client patterns
  3. Register in `multi_llm_router.py` `_get_client()` method
  4. Update `_detect_provider()` for auto-detection from model strings
