# EmotiCoach

EmotiCoach is a Flutter mobile application designed to help users become better communicators. It connects to the user's Telegram account, reads their conversations, detects the emotional tone of messages using AI, and provides context-aware reply suggestions powered by a Retrieval-Augmented Generation (RAG) pipeline. Users can also practice real-world communication scenarios through AI role-play and earn XP/achievements as they improve.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Backend Architecture](#backend-architecture)
  - [Entry Point](#entry-point)
  - [API Routes](#api-routes)
  - [Emotion Detection Pipeline](#emotion-detection-pipeline)
  - [RAG Pipeline (Reply Suggestions)](#rag-pipeline-reply-suggestions)
  - [Scenario Role-Play Engine](#scenario-role-play-engine)
  - [Telegram Integration](#telegram-integration)
  - [Database](#database)
  - [Caching Layer (Redis)](#caching-layer-redis)
  - [File Storage (Supabase)](#file-storage-supabase)
  - [Gamification](#gamification)
- [Environment Variables](#environment-variables)
- [Running the Backend](#running-the-backend)
- [Running with Docker](#running-with-docker)
- [Flutter Frontend](#flutter-frontend)

---

## Features

- **Telegram Message Analysis** — Syncs messages via the Telegram API and stores them with semantic and emotion embeddings.
- **Emotion Detection** — Classifies each message into one of seven emotions: *anger, disgust, fear, joy, neutral, sadness, surprise*.
- **AI Reply Suggestions** — Generates contextually appropriate, emotionally-aware reply suggestions using a RAG pipeline backed by Groq LLMs.
- **Filipino/Taglish Support** — Automatically translates Filipino and Taglish text to English before emotion analysis to preserve accuracy.
- **Communication Scenarios** — Guided AI role-play scenarios (e.g., job interviews, conflict resolution) with real-time scoring.
- **Gamification** — XP system, level progression, badges, and daily challenges.
- **Overlay Mode** — A floating overlay window that surfaces reply suggestions while the user is in another app.
- **Reading Module** — An integrated EPUB reader with reading progress tracking.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile Frontend | Flutter (Dart) |
| Backend API | Python 3.11 + FastAPI + Uvicorn |
| Database | PostgreSQL (SQLModel / SQLAlchemy) |
| Cache | Redis |
| File Storage | Supabase (S3-compatible) |
| Auth | Firebase Authentication |
| Messaging | Telethon (Telegram MTProto) |
| Emotion Model | `j-hartmann/emotion-english-roberta-large` (HuggingFace Inference API) |
| Semantic Embeddings | `BAAI/bge-m3` (HuggingFace Inference API, 1024-dim) |
| Reranker | `BAAI/bge-reranker-v2-m3` (HuggingFace Inference API) |
| LLM (replies & translation) | Groq (configurable model) |
| Local Classifier | Custom fine-tuned HuggingFace model (stored in `Backend/AIModel`) |
| Containerisation | Docker |

---

## Project Structure

```
emoticoach1/
├── Backend/                  # Python FastAPI backend
│   ├── main.py               # App entry point, router registration
│   ├── Dockerfile            # Container definition
│   ├── core/                 # DB connection, Supabase config
│   ├── routes/               # FastAPI routers (one file per feature area)
│   ├── services/             # Business logic & AI pipelines
│   ├── model/                # SQLModel ORM table definitions
│   ├── utilities/            # Helper scripts (PDF, image upload, etc.)
│   └── AIModel/              # Local HuggingFace model weights
├── lib/                      # Flutter application source
│   ├── main.dart
│   ├── screens/
│   ├── controllers/
│   ├── services/
│   ├── models/
│   ├── widgets/
│   └── utils/
├── assets/                   # Images, icons, fonts, sample EPUB files
├── pubspec.yaml              # Flutter dependencies
└── README.md
```

---

## Backend Architecture

### Entry Point

**`Backend/main.py`** bootstraps the FastAPI application:

1. Loads environment variables from `.env` via `python-dotenv`.
2. Creates the `FastAPI` application instance with CORS middleware (open to all origins for development).
3. Registers all feature routers under their respective URL prefixes.
4. Exposes `/` (root ping) and `/health` health-check endpoints.
5. When run directly, starts Uvicorn on `0.0.0.0:$PORT` (defaults to `8000`).

In production (Docker), the `CMD` directive starts Uvicorn with **6 workers**.

---

### API Routes

| Prefix | File | Description |
|---|---|---|
| `/messages` | `message_routes.py` | Telegram session management, message fetching, emotion summaries |
| `/rag` | `rag_routes.py` | AI reply suggestion generation, emotion analysis endpoints |
| `/scenarios` | `scenario_route.py` | Role-play scenario CRUD, AI chat, evaluation |
| `/books` | `book_routes.py` | Book library management |
| `/userinfo` | `userinfo_routes.py` | User profile read/write |
| `/experience` | `experience_routes.py` | XP and level progression |
| `/achievements` | `user_achievement_routes.py` | Badge and achievement tracking |
| `/overlay-stats` | `overlay_stats_routes.py` | Floating overlay usage statistics |
| `/cache` | `cache_routes.py` | Cache inspection and invalidation |
| `/support` | `support_routes.py` | In-app support messages |
| `/daily` | `daily_routes.py` | Daily challenge management |
| `/stats` | `stat_routes.py` | Aggregated user statistics |

---

### Emotion Detection Pipeline

**`Backend/services/emotion_pipeline.py`** — `EmotionEmbedder` class

The emotion pipeline converts any text (including Filipino and Taglish) into a 7-dimensional emotion vector.

```
Input text
    │
    ▼
[Translation step — if non-English]
Groq LLM translates text to English while preserving
emotional intensity, informal register, and punctuation
    │
    ▼
[Emotion classification]
j-hartmann/emotion-english-roberta-large
(via HuggingFace Inference API)
Outputs probability scores for:
  anger · disgust · fear · joy · neutral · sadness · surprise
    │
    ▼
[Output]
{
  "dominant_emotion": "sadness",
  "emotion_scores": { "joy": 0.02, "sadness": 0.81, ... },
  "embedding": [0.02, 0.01, 0.03, 0.02, 0.04, 0.81, 0.07]
}
```

The detected dominant emotion drives the **response tone policy**:

| Emotion | Response Tone |
|---|---|
| anger | Calm |
| sadness | Encouraging |
| fear | Reassuring |
| disgust | Understanding |
| joy | Supportive |
| neutral | Reflective |
| surprise | Supportive |

A **local HuggingFace model** (`Backend/AIModel`) is also available for offline/batch classification via `AI_inferenece.py` (used by `analyze_file` for bulk message analysis).

---

### RAG Pipeline (Reply Suggestions)

**`Backend/services/RAGPipeline.py`** — `SimpleRAG` class

The RAG pipeline retrieves emotionally-relevant knowledge and generates a human-like reply suggestion.

```
User message (latest message from contact)
    │
    ├──[1. Dual Embedding]
    │       ├─ Semantic embedding  (BAAI/bge-m3, 1024-dim) via HF Inference API
    │       └─ Emotion embedding   (7-dim probability vector from EmotionEmbedder)
    │
    ├──[2. Hybrid Similarity Search]
    │       Combined score = 0.7 × semantic_cosine + 0.3 × emotion_cosine
    │       Retrieves top-10 candidate documents
    │
    ├──[3. Reranking]
    │       BAAI/bge-reranker-v2-m3 scores each (query, document) pair
    │       Final score = 0.4 × similarity + 0.6 × rerank_score
    │       Returns top-3 documents
    │
    ├──[4. Prompt Construction]
    │       System prompt includes:
    │         • Response tone instruction (from emotion → tone policy)
    │         • Problem-solving guidance (for negative emotions)
    │         • Length instruction (casual / question / task)
    │         • Strict no-profanity rule
    │       User prompt includes:
    │         • User's past message style examples
    │         • Conversation history
    │         • Retrieved knowledge context
    │         • The latest contact message to reply to
    │
    └──[5. LLM Generation]
            Groq API (configurable model)
            temperature=0.85, dynamic max_tokens (50–500)
            Post-processed: quote stripping, prefix removal, profanity filter
```

**Length heuristic** (`_get_length_instruction`): the route layer classifies the incoming message as a *task*, *question*, or *casual* message and passes a corresponding `length_instruction` to the RAG, which adjusts `max_tokens` (500 / 100 / 50 respectively).

**Profanity filter**: a hardcoded list of English and Filipino curse words is applied as a post-generation regex filter. If the entire output is filtered, it falls back to `"I understand how you feel."`.

---

### Scenario Role-Play Engine

**`Backend/services/scenario.py`**

Scenarios are YAML-based configurations stored in Supabase Storage. Each scenario defines a character persona, conversation objectives, and scoring rubrics. The service uses **LlamaIndex + Groq** to:

1. Load the scenario configuration and inject the character persona into the system prompt.
2. Maintain a multi-turn conversation history.
3. After the conversation ends, evaluate the user's performance across four dimensions: **Clarity**, **Empathy**, **Assertiveness**, and **Appropriateness**.
4. Persist the completion record (scores, duration, message count) to the `ScenarioCompletion` table.

---

### Telegram Integration

**`Backend/services/messages_services.py`** uses **Telethon** (MTProto client) to:

- Authenticate users and persist Telegram sessions as encrypted strings in the `TelegramSession` database table.
- Fetch conversation history with a given contact.
- Store each fetched message with its **semantic embedding** (from `bge-m3`) and **emotion embedding** (from `EmotionEmbedder`) in the `Message` table for later RAG retrieval and analytics.
- Manage in-memory client instances (`active_clients` dict) with per-user `asyncio.Lock`s for thread-safe access.

---

### Database

**`Backend/core/db_connection.py`**

- Driver: `psycopg2` via SQLAlchemy / SQLModel.
- Connection pool: size 10, max overflow 20, 1-hour recycle, pre-ping enabled.
- Tables are auto-created on startup via `SQLModel.metadata.create_all(engine)`.

Key tables (defined under `Backend/model/`):

| Model | Purpose |
|---|---|
| `UserInfo` | User profile (name, phone number) |
| `Message` | Stored Telegram messages with embeddings |
| `TelegramSession` | Persisted Telethon string sessions |
| `ExperienceInfo` | User XP totals |
| `LevelSystem` | XP thresholds and level metadata |
| `UserAchievement` | Earned badges |
| `ScenarioWithConfig` | Scenario definitions and config file paths |
| `ScenarioCompletion` | Per-user scenario results |
| `ReadingsInfo` / `ReadingBlock` | Book library and reading progress |

---

### Caching Layer (Redis)

**`Backend/services/cache.py`** — `MessageCache` class

Redis is used to reduce repeated database queries and model inference calls:

| Cache Key Type | TTL |
|---|---|
| Messages | 5 minutes |
| User info | 1 hour |
| Emotion analysis results | 10 minutes |
| Conversation context | 3 minutes |

Redis can be configured via `REDIS_URL` (full connection string) or individual `REDIS_HOST` / `REDIS_PORT` / `REDIS_USERNAME` / `REDIS_PASSWORD` variables. SSL support is toggled via `REDIS_USE_SSL`.

---

### File Storage (Supabase)

**`Backend/core/supabase_config.py`** — `SupabaseStorage` class

Scenario YAML configuration files and user-uploaded images are stored in Supabase Storage via the S3-compatible API (using `boto3`). Presigned URLs (1-hour expiry) are used to serve private assets.

---

### Gamification

- **XP & Levels** (`experience_service.py`, `LevelSystem` model): After completing scenarios or daily challenges, the user earns XP. The level system maps XP thresholds to level numbers, names, and badge images.
- **Achievements** (`user_achievement_routes.py`): Unlocked based on milestones (e.g., completing a first scenario, reaching a level).
- **Daily Challenges** (`daily_routes.py`, `daily_service.py`): Time-gated tasks that refresh each day.
- **Statistics** (`stat_routes.py`, `stat_service.py`): Aggregate emotion distribution, scenario scores, and reading progress for display in the app's dashboard.

---

## Environment Variables

Create a `.env` file in `Backend/` with the following keys:

```env
# Database
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=5432
DB_NAME=

# Redis
REDIS_URL=                  # Optional: full Redis connection string
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_USE_SSL=false

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=
SUPABASE_STORAGE_ACCESS_KEY=
SUPABASE_STORAGE_SECRET_KEY=

# Telegram (Telethon)
api_id=
api_hash=

# HuggingFace
HF_API_KEY=                 # Used for bge-m3 and reranker
HF_TOKEN=                   # Used for emotion model (j-hartmann)

# Groq
api_key=                    # Groq API key
model=                      # Groq model name (e.g. llama3-8b-8192)

# Server
PORT=8000
```

---

## Running the Backend

```bash
cd Backend
pip install -r requirements.txt
python main.py
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## Running with Docker

```bash
cd Backend
docker build -t emoticoach-backend .
docker run -p 8000:8000 --env-file .env emoticoach-backend
```

The container runs Uvicorn with **6 workers** by default.

---

## Flutter Frontend

The Flutter app is located in `lib/` and uses:

- **Firebase Auth** — Email/password and Google Sign-In.
- **HTTP package** — Communicates with the FastAPI backend.
- **flutter_overlay_window** — Floating reply-suggestion overlay while using Telegram.
- **epub_view / flutter_epub_viewer** — In-app EPUB reading.
- **fl_chart** — Emotion distribution and progress charts.
- **provider** — State management.

To run the Flutter app:

```bash
flutter pub get
flutter run
```

Ensure the backend URL is configured in `lib/config/` and that a valid Firebase project is set up with `google-services.json` (Android) and `GoogleService-Info.plist` (iOS) in place.
