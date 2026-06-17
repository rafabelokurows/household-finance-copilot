# Deployment Options — 2026-06-06

Stack: FastAPI backend + SQLite + Gemini API + React (Vite) frontend.

## Known constraints

- SQLite needs **persistent disk** — rules out purely serverless hosts
- Gmail `token.json` must persist between restarts (can't commit it)
- Gemini API key must be set as an env var
- `docker-compose.yml` currently references old Streamlit frontend — needs updating before any Docker-based deploy

---

## Option A: Railway (both services)

Single platform for frontend and backend. Persistent disk available for SQLite. Auto-deploy from GitHub. Docker or nixpacks auto-detection. ~$5/mo after free trial.

**Pros:** Least moving parts, one dashboard, easy env vars, persistent volumes.  
**Cons:** Frontend served from same region as backend (no global CDN).

---

## Option B: Vercel (frontend) + Railway (backend) ⭐ recommended

Vercel deploys the Vite/React build as a static site — global CDN, instant cache invalidation, free forever. Railway runs the FastAPI backend with a persistent volume for SQLite.

**Pros:** Best frontend performance, free frontend tier, clean separation.  
**Cons:** Two platforms to manage. `VITE_API_BASE` env var must point to Railway backend URL.  
**Cost:** ~$5/mo (Railway backend only).

---

## Option C: Fly.io (both services)

More control, persistent volumes, generous free tier. Requires `fly.toml` config per service.

**Pros:** Good free tier, persistent volumes, multi-region if needed.  
**Cons:** More config work upfront, less beginner-friendly dashboard.

---

## Decision

- [ ] Option A — Railway (both)
- [ ] Option B — Vercel + Railway
- [ ] Option C — Fly.io
