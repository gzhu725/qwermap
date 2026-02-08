# QwerMap Setup Guide

## Prerequisites

- Docker & Docker Compose
- Solana CLI (for keypair generation)

## 1. Generate Solana Keypair

```bash
mkdir -p keys
solana-keygen new --outfile ./keys/devnet.json --no-bip39-passphrase
solana airdrop 2 --keypair ./keys/devnet.json --url devnet
```

## 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `VITE_MAPBOX_TOKEN` — Get one at https://account.mapbox.com/access-tokens/
- `VITE_GOOGLE_GENERATIVE_AI_API_KEY` — Get one at https://aistudio.google.com/apikey

## 3. Build & Run

```bash
docker compose up --build
```

This starts:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/v1
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379

The `mongo-seed` service automatically inserts 18 demo LGBTQ+ places around LA.

## 4. Verify

1. Open http://localhost:3000 — map should show 18 places around West Hollywood / LA
2. Click a marker to view place details
3. Submit a new place via the form — it should appear immediately
4. Upvote a place — toast shows the Solana transaction ID
5. Toggle the safety heatmap layer

## Troubleshooting

- **Seed didn't run?** Check logs: `docker compose logs mongo-seed`
- **API errors?** Check: `docker compose logs api`
- **Solana errors?** Ensure `./keys/devnet.json` exists and has SOL: `solana balance --keypair ./keys/devnet.json --url devnet`
