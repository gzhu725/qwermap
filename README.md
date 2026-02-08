# QWERMaps

An interactive map for discovering and preserving LGBTQ+ third places — bars, cafes, libraries, community centers, and historical sites that serve as vital gathering spaces for queer communities.

Every place submission is recorded on the **Solana blockchain** for transparent, tamper-proof preservation. Community upvotes drive a safety score, and an AI-powered guide (Gemini) helps users explore movements, figures, and history.

![QWERMap Screenshot](docs/screenshot.png)

## Features

- **Interactive Map** — Browse LGBTQ+ places on a Mapbox-powered map with clustering, category-colored markers, and 3D building view
- **Place Submissions** — Submit new places with descriptions, historical events, related figures, movement tags, and community labels
- **Solana Verification** — Every submission and upvote is recorded as a memo transaction on Solana Devnet
- **Safety Heatmap** — Toggle a heatmap layer showing community-derived safety scores across regions
- **AI Guide** — Chat with a Gemini-powered assistant to explore LGBTQ+ history, find places, discover figures, and browse timelines
- **Search & Filter** — Filter by category (bar, cafe, library, etc.), type (current/historical), and sort by upvotes, safety, or distance
- **Featured Places** — Randomized featured section highlighting notable locations
- **Mobile-Responsive** — Full mobile drawer with tabbed navigation for all features

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, TailwindCSS 4 |
| Routing | TanStack Router |
| State | Zustand |
| Map | Mapbox GL JS, Supercluster |
| Animations | Framer Motion |
| AI Chat | Vercel AI SDK + Google Gemini |
| Backend | Python, Flask, Gunicorn |
| Database | MongoDB 7 (MongoEngine ODM) |
| Cache | Redis 7 |
| Blockchain | Solana (SPL Memo Program) |
| Containers | Docker Compose |

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Solana CLI](https://docs.solanalabs.com/cli/install) (for keypair generation)

### 1. Clone the repository

```bash
git clone --recurse-submodules https://github.com/your-org/qwermap.git
cd qwermap
```

> The frontend lives in the `qwermap-ui` git submodule. The `--recurse-submodules` flag ensures it's pulled automatically.

### 2. Generate a Solana keypair

```bash
mkdir -p keys
solana-keygen new --outfile ./keys/devnet.json --no-bip39-passphrase
solana airdrop 2 --keypair ./keys/devnet.json --url devnet
```

This creates a devnet wallet used to sign place submissions and upvotes on-chain.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it |
|----------|----------------|
| `VITE_MAPBOX_TOKEN` | [Mapbox Access Tokens](https://account.mapbox.com/access-tokens/) |
| `VITE_GOOGLE_GENERATIVE_AI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |

### 4. Build and run

```bash
docker compose up --build
```

This starts five services:

| Service | URL | Description |
|---------|-----|-------------|
| **ui** | http://localhost:3000 | React frontend |
| **api** | http://localhost:8000/v1 | Flask REST API |
| **mongo** | localhost:27017 | MongoDB database |
| **redis** | localhost:6379 | Rate limiting cache |
| **mongo-seed** | (runs once) | Seeds 18 demo places around LA |

### 5. Verify it works

1. Open http://localhost:3000 — you should see markers around West Hollywood / LA
2. Click a marker to view place details, events timeline, and on-chain transaction ID
3. Submit a new place via the **Add** tab — it records a Solana transaction
4. Upvote a place — a toast shows the Solana transaction ID
5. Toggle the **Safety Map** button in the header to see the heatmap overlay

## Project Structure

```
qwermap/
├── backend/                  # Python Flask API
│   ├── app.py               # Flask entry point
│   ├── config.py            # Environment config
│   ├── db.py                # MongoDB connection
│   ├── models.py            # MongoEngine document models
│   ├── seed.py              # Database seeder (18 LA places)
│   ├── routes/
│   │   ├── places.py        # GET/POST /v1/places
│   │   ├── interactions.py  # POST /v1/places/:id/upvote
│   │   ├── safety.py        # GET /v1/safety-scores
│   │   └── moderation.py    # Moderation queue endpoints
│   ├── services/
│   │   ├── solana_service.py # Solana transaction signing
│   │   └── rate_limit.py    # Redis-based rate limiting
│   └── utils/
│       ├── validation.py    # Input validation & enums
│       └── errors.py        # Error response formatting
├── qwermap-ui/              # React frontend (git submodule)
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── routes/          # TanStack Router pages
│   │   ├── store/           # Zustand state stores
│   │   ├── hooks/           # Custom React hooks
│   │   ├── api/             # API client layer
│   │   ├── types/           # TypeScript types
│   │   └── styles.css       # Theme & global styles
│   └── Dockerfile
├── keys/                    # Solana keypair (gitignored)
├── docker-compose.yml       # Full-stack orchestration
├── backend-spec.yaml        # OpenAPI 3.0.3 specification
└── .env.example             # Environment variable template
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/places?lat=&lon=` | Get places near coordinates |
| `GET` | `/v1/places/:id` | Get place details |
| `POST` | `/v1/places` | Submit a new place (Solana-backed) |
| `POST` | `/v1/places/:id/upvote` | Upvote a place (Solana-backed) |
| `GET` | `/v1/safety-scores?lat=&lon=` | Aggregated regional safety score |
| `GET` | `/v1/safety-scores/heatmap?lat=&lon=` | Heatmap grid data |
| `GET` | `/v1/moderation/queue` | Pending submissions |
| `PATCH` | `/v1/moderation/places/:id` | Approve/reject a submission |

Full API specification: [`backend-spec.yaml`](backend-spec.yaml)

## Local Development (without Docker)

If you prefer running services locally:

**Backend:**

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env.local  # edit with your local MongoDB/Redis URIs
python app.py
```

**Frontend:**

```bash
cd qwermap-ui
npm install        # or: bun install
cp .env.example .env.local
npm run dev        # starts on http://localhost:3000
```

You'll need MongoDB and Redis running locally (or update the connection strings to point to hosted instances).

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Seed data didn't load | `docker compose logs mongo-seed` |
| API errors | `docker compose logs api` |
| Solana transaction failures | Check balance: `solana balance --keypair ./keys/devnet.json --url devnet` |
| Map doesn't render | Verify `VITE_MAPBOX_TOKEN` is set in `.env` |
| AI chat not responding | Verify `VITE_GOOGLE_GENERATIVE_AI_API_KEY` is set in `.env` |
| Port conflicts | Stop other services on ports 3000, 8000, 27017, or 6379 |

## License

MIT
