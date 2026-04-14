# Testing

**Project Experience Explorer — CS 467 Spring 2026**

> **Status: Placeholder — to be filled in as tests are written**

---

## Overview

> Document the testing approach here once tests are written. Include what framework is used, what is tested, and how to run tests.

---

## Running Tests

> Add instructions here once tests exist.

```bash
# placeholder — update when tests are written
python -m pytest
```

---

## Test Structure

> Document the test folder structure here once it exists.

```
/tests
    test_routes.py        # Flask route tests
    test_db.py            # Database query tests
    test_auth.py          # Auth flow tests (when ONID is implemented)
```

---

## What to Test

> Fill this in as features are built. General guidelines:

- Every Flask route should have at least a smoke test (does it return 200?)
- Database functions should be tested with a test database, not production
- Form submissions should be tested for both valid and invalid input
- Auth-protected routes should be tested for both authenticated and unauthenticated access

---

## Test Database

> Document how to set up a test database here once the approach is decided.

Options being considered:
- Separate local MySQL database for testing
- In-memory SQLite for unit tests
- Fixtures/mocks for database calls

---

## CI Integration

Tests will be added to the GitHub Actions lint workflow once written. Every PR will need to pass tests before merging.

> Update `.github/workflows/lint.yml` when tests are added.

---

## Open Questions

- [ ] What testing framework? (pytest recommended for Flask)
- [ ] How to handle database in tests — mock, fixture, or separate test DB?
- [ ] What coverage percentage is the team targeting?
