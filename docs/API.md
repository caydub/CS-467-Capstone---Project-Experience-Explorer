# API Reference

**Project Experience Explorer — CS 467 Spring 2026**

This is a living document. Add new routes here as they are built.

---

## Overview

The app uses server-rendered pages via Flask and Jinja2 templates. There is no separate REST API — routes return HTML pages, not JSON. All data is passed from Flask routes directly to templates via `render_template()`.

Routes that modify data (forms, votes, comments) use HTTP POST. Routes that display data use HTTP GET.

---

## Authentication

ONID/CAS authentication is a bonus feature. Until it is implemented, review submission is open.

Once implemented:
- Unauthenticated users can browse and read reviews
- Authenticated users (ONID login) can submit reviews, rate helpfulness, and comment
- No personal data is stored — only a hashed identifier and pseudonym

---

## Routes

### Public Routes (no login required)

| Method | Route | Description | Template | Status |
|--------|-------|-------------|----------|--------|
| GET | `/` | Homepage — project listing with search and filter | `index.html` | 🔲 not built |
| GET | `/projects` | Browse all projects | `projects.html` | 🔲 not built |
| GET | `/projects/<id>` | Project detail page — all reviews for a project | `project_detail.html` | 🔲 not built |

---

### Auth Routes

| Method | Route | Description | Template | Status |
|--------|-------|-------------|----------|--------|
| GET | `/login` | Redirect to ONID/CAS login | — | 🔲 not built |
| GET | `/logout` | Clear session and redirect to homepage | — | 🔲 not built |
| GET | `/auth/callback` | CAS callback — handle login response | — | 🔲 not built |

---

### Review Routes (login required)

| Method | Route | Description | Template | Status |
|--------|-------|-------------|----------|--------|
| GET | `/reviews/new/<project_id>` | Review submission form for a project | `review_form.html` | 🔲 not built |
| POST | `/reviews/new/<project_id>` | Submit a review | — | 🔲 not built |

---

### Helpfulness Routes (login required)

| Method | Route | Description | Template | Status |
|--------|-------|-------------|----------|--------|
| POST | `/reviews/<review_id>/helpful` | Upvote a review as helpful | — | 🔲 not built |
| POST | `/reviews/<review_id>/not-helpful` | Downvote a review | — | 🔲 not built |

---

### Comment Routes (login required)

| Method | Route | Description | Template | Status |
|--------|-------|-------------|----------|--------|
| POST | `/reviews/<review_id>/comments` | Submit a comment on a review | — | 🔲 not built |

---

### Dev/Debug Routes (remove before final demo)

| Method | Route | Description | Status |
|--------|-------|-------------|--------|
| GET | `/test-db` | Test database connection | ✅ built — remove before demo |

---

## Status Key

| Symbol | Meaning |
|--------|---------|
| ✅ | Built and working |
| 🔲 | Not built yet |
| 🚧 | In progress |
| ❌ | Removed |

---

## Notes for Contributors

- Follow PEP 8 for all route functions
- Every route that queries the database must call `get_db_connection()` and close the connection when done
- Use `render_template()` for all responses — no raw HTML strings in routes
- POST routes that modify data should redirect after success (POST/Redirect/GET pattern) to prevent duplicate submissions on refresh
- Add new routes to this doc when you build them — update the status as you go
