# AI Image Generator — Design Spec

**Date:** 2026-06-21  
**Model:** Runware klingai-image-3-0  
**Stack:** Static HTML + FastAPI on Railway + PostgreSQL

---

## Goal

Add a new page to the existing site with a full-featured AI image generation tool.  
Primary user: the site owner (free). Secondary users: paying clients (manual account creation).

---

## Architecture

```
Frontend (static HTML, deployed with main site)
  image-gen/index.html   — generator page
  image-gen/login.html   — login
  image-gen/admin.html   — admin panel (owner only)

Backend (new Railway service)
  main.py                — FastAPI app
  models.py              — SQLAlchemy models
  requirements.txt
```

Frontend calls Backend API via fetch. Backend calls Runware API and stores results in PostgreSQL.

---

## Backend API

| Method | Route | Access | Description |
|--------|-------|--------|-------------|
| POST | /api/login | public | Returns JWT token |
| POST | /api/generate | user | Call Runware, save to DB, deduct credits |
| GET | /api/history | user | User's past generations |
| GET | /api/gallery | user | All user images (paginated) |
| POST | /api/admin/users | admin | Create client account |
| PUT | /api/admin/users/{id}/credits | admin | Add/set credits |
| GET | /api/admin/users | admin | List all users + credit balances |

Auth: JWT in Authorization header. Admin flag checked server-side.

---

## Database (PostgreSQL on Railway)

**users**
- id, username, password_hash, credits (int), is_admin (bool), created_at

**generations**
- id, user_id, prompt, negative_prompt, settings (JSON), image_urls (JSON array), created_at

Images are hosted by Runware — we only store URLs.

---

## Frontend Pages

**login.html** — username + password form, stores JWT in localStorage.

**index.html** (generator) — two-column layout:
- Left: prompt textarea, negative prompt, size select, count select, CFG scale slider, steps slider, Generate button, credits counter
- Right: tabs (Результат / История / Галерея), generated images with download buttons, history list with re-use button

**admin.html** — table of users with credits, form to create new user, input to add credits to existing user.

---

## Credit System

- Owner account: unlimited (is_admin = true, credits not checked)
- Client accounts: credits deducted per image generated (1 image = 1 credit, задаётся константой в коде)
- If credits = 0, generate button is disabled with message
- Owner adds credits manually via admin panel after receiving payment

---

## Deployment

- Backend: new Railway service, same project as audit-bot
- PostgreSQL: Railway plugin (shared or separate DB)
- Frontend: static files added to existing site repo, deployed via Netlify
- Runware API key stored as Railway environment variable

---

## Out of Scope

- Automatic payment processing (manual credit top-up only)
- Email notifications
- Image editing or upscaling
- Multiple AI models (only klingai-image-3-0 for now)
