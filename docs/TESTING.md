# Testing

**OSU Capstone Explorer — CS 467 Spring 2026**

> **Status: Current as of May 2026**

---

## Overview

Tests are written with pytest and cover route smoke tests and auth helper functions. The test suite uses a mock database connection so no live Cloud SQL instance is needed to run tests.

---

## Running Tests

Make sure you're in the project root with the virtual environment active:

```bash
source .venv/bin/activate
python -m pytest tests/
```

To see verbose output:

```bash
python -m pytest tests/ -v
```

---

## Test Structure

```
tests/
    conftest.py       # Shared fixtures — Flask test client, mock DB connection
    test_routes.py    # Smoke tests for all routes, login redirect behavior
    test_auth.py      # get_or_create_student logic, ONID hashing, pseudonym uniqueness
```

---

## What Is Covered

**Route tests (`test_routes.py`)**
- All public routes return 200
- Auth-protected routes redirect unauthenticated users to /login
- Routes that require a valid project_id return 404 on bad input

**Auth tests (`test_auth.py`)**
- `get_or_create_student` creates a new student on first login
- `get_or_create_student` returns the existing student on repeat login
- ONID hashing is consistent — same email always produces the same hash
- Pseudonym uniqueness retry — if a generated pseudonym is already taken, a new one is generated

---

## CI Integration

flake8 runs on every PR via GitHub Actions (`.github/workflows/lint.yml`). Tests are not currently wired into CI but can be run locally before opening a PR.

---

## Test Database

Tests use `unittest.mock` to patch `get_db_connection()` so no database connection is required. Mock return values are set per test to simulate query results.
