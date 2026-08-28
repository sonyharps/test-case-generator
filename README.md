# AI Test Case Generator

Platform QA otomatis yang mengubah dokumen requirement (PRD, User Story, Figma Flow) menjadi **test case production-grade** sesuai standar **ISO/IEC/IEEE 29119-3** — lengkap dengan RBAC, RAG exemplar learning, dan export Excel/PDF.

> Dari PRD menjadi **200+ test case dalam ±2 menit, biaya ±Rp 150 per generate**.

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **Pipeline v8-Parallel** | 4 LLM call konkuren (Functional, Negative, Boundary, Summary+Risk) — volume 3x lipat dengan waktu tempuh hampir sama |
| **Standar ISO/IEC/IEEE 29119-3** | 9 field per test case: Priority (P0-P3), Module (traceability), Preconditions, Test Data, Steps, Expected Result **per-step**, Postconditions |
| **Teknik desain 29119-4** | Equivalence Partitioning, Boundary Value Analysis (min/max±1), Error Guessing (XSS/SQLi), State Transition — embedded di prompt tiap kategori |
| **RAG Exemplar Learning** | Generate "belajar dari riwayat" — TC serupa dari generate sebelumnya di-inject sebagai acuan gaya (anti-duplikat ketat, user-scoped) |
| **Multi-Provider LLM** | OpenRouter (300+ model), GLM/Z.AI, Gemini, Groq — ganti model tinggal ganti dropdown |
| **Multi-Dokumen** | Gabungkan PRD + User Story + Figma Flow dalam satu generate |
| **PII Redaction** | NIK, no rekening, kartu, email, IP, token otomatis di-mask **sebelum** teks dikirim ke LLM cloud |
| **RBAC + Squad** | 4 role (admin/kabag/qa_lead/qa_staff) + squad-based data scoping, user & squad management UI |
| **Volume Preset** | Standard (~90 TC) · Large (~140) · Max (~200+) |
| **Export** | Excel multi-sheet styled (priority color-coded) & PDF profesional |
| **Approval Workflow** | Review, edit inline, approve/reject, threaded comments |
| **Cache** | Hasil generate di-cache Redis 7 hari — request sama = instan |

## 🏗️ Arsitektur

```
┌─────────────────────────────────────────────────────────┐
│  Frontend — React 19 + TypeScript + Zustand + Tailwind  │
│  (Orchestrator, History, Documents, Admin, Analytics)   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS + JWT
┌────────────────────────▼────────────────────────────────┐
│  Backend — FastAPI (async)                              │
│  ├─ REST API /v1 (auth, orchestrator, documents, ...)   │
│  ├─ RBAC Guard (4 role + squad scoping)                 │
│  ├─ Redis Cache (7 hari)                                │
│  └─ PIPELINE v8-PARALLEL:                               │
│     1. Multi-doc input → 2. PII Redaction 🔒            │
│     3. 4 LLM call paralel ⚡ → 4. Validasi + salvage    │
│     5. Output 29119-3 (Excel/PDF)                       │
└───────┬─────────────┬──────────────┬────────────────────┘
        │             │              │
   ┌────▼────┐   ┌────▼─────┐   ┌────▼─────────────┐
   │ Postgres │   │  Qdrant  │   │ LLM Cloud        │
   │ (data)   │   │ (vector) │   │ via OpenRouter   │
   └──────────┘   └──────────┘   │ Qwen3.7 Flash 🏆 │
                                  │ Gemini 2.5 ⚡    │
                                  │ GPT-OSS 120B     │
                                  └──────────────────┘
```

**Stack:** FastAPI · SQLAlchemy async · PostgreSQL · Redis · Qdrant (embedding Gemini 3072-dim) · React 19 · Vite · Zustand · TailwindCSS · openpyxl

## 📊 Benchmark (volume Max, dokumen PRD 15k chars)

| Model | Test Case | Waktu | Token | Biaya/generate |
|-------|-----------|-------|-------|----------------|
| **Qwen3.7 Flash** 🏆 default | 205 | 2.3 mnt | 80.4k | **$0.009 (≈Rp 150)** |
| Gemini 2.5 Flash ⚡ | 200 | 1.4 mnt | 78.4k | ~$0.15 |
| GPT-OSS 120B | 205 | 6.3 mnt | 60.3k | $0.008 |
| Qwen3 Next 80B | 249 | 4.2 mnt | 83.4k | $0.07 |

**Formula token:** `total ≈ 21.000 (prompt) + (350 × jumlah TC)`

## 🚀 Menjalankan Project

### Prasyarat
- Python 3.12+ & venv
- Node.js 20+
- Docker (PostgreSQL, Redis, Qdrant)

### 1. Services (Docker)
```bash
docker compose up -d          # postgres :5432, redis :6379, qdrant :6333
```

### 2. Environment
```bash
cp .env.example .env
# isi minimal: SECRET_KEY, DATABASE_URL, dan salah satu: OPENROUTER_API_KEY / GLM_API_KEY
```
API keys: [OpenRouter](https://openrouter.ai/keys) · [Z.AI/GLM](https://z.ai) · [Gemini](https://aistudio.google.com/apikey)

### 3. Database Migration
```bash
venv/bin/alembic upgrade head
```

### 4. Backend
```bash
python -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
# API docs: http://localhost:8000/docs
```

### 5. Frontend
```bash
cd web && npm install && npm run dev
# http://localhost:5173
```

### 6. Admin Pertama
```bash
venv/bin/python scripts/create_admin.py <username> <email> <password>
```

## 📖 Penggunaan

1. **Login** → pilih **Provider** (OpenRouter recommended) & model (Qwen3.7 Flash 🏆)
2. **Upload dokumen** di menu Documents (PRD/user story/figma flow, multi-select)
3. Di Orchestrator: pilih dokumen, **Volume** (Standard/Large/Max), toggle **"Belajar dari riwayat"**
4. **Generate** → 90-200+ test case siap dalam 1-3 menit
5. **Export** Excel/PDF dari hasil atau dari Session History

## 🔌 API Utama

| Endpoint | Fungsi |
|----------|--------|
| `POST /v1/auth/login` | JWT auth |
| `POST /v1/documents/upload` | Upload & proses dokumen (auto-embed) |
| `POST /v1/orchestrator/run` | Generate TC — params: `document_ids`, `targets`, `use_history`, `model` |
| `GET /v1/history/sessions` | Riwayat (scoped by role/squad) |
| `POST /v1/orchestrator/excel` / `/pdf` | Export report |
| `GET/POST /v1/users`, `/v1/squads` | User & squad management (kabag+) |

## 📁 Struktur Project

```
app/
├── api/v1/               # Routers (auth, orchestrator, documents, users, squads, ...)
├── api/deps/             # RBAC dependencies (require_role, get_data_scope)
├── pipeline/
│   ├── orchestrator_v8.py    # Pipeline paralel utama
│   ├── prompt_builder/       # v8 category + summary prompts (29119-3)
│   ├── postprocessor/        # parser + salvage + validator
│   └── exporter/             # Excel exporter
├── services/
│   ├── exemplar_service.py   # RAG exemplar learning (index + retrieve)
│   ├── pii_redactor.py       # PII masking sebelum ke LLM
│   └── session_service.py    # Persist session + TC
├── models/                # SQLAlchemy (User, Squad, Session, TestCase, ...)
└── db/                    # Async engine & session
web/src/                   # React 19 (pages, components, store, api)
alembic/versions/          # Migrations 001-006
scripts/                   # create_admin, benchmark, quality_audit
```

## 🔒 Keamanan

- **PII redaction** sebelum teks keluar ke LLM cloud (NIK, rekening, kartu, email, IP, token)
- **RBAC 4-role** + squad scoping di level query (qa_lead lihat squad-nya, kabag/admin semua)
- History retrieval **user-scoped** — prompt tidak pernah berisi TC user lain
- `.env` tidak di-track; API key tidak pernah masuk git history

## 🌿 Branching

| Branch | Isi |
|--------|-----|
| `main` | Baseline |
| `feature/orchestrator-v8` | RBAC + OpenRouter + v8-parallel + 29119-3 + volume knob |
| `feature/rag-exemplar-learning` | RAG exemplar learning (belajar dari riwayat) |
