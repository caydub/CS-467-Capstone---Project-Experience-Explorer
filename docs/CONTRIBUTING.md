# Contributing

**Project Experience Explorer — CS 467 Spring 2026**

Guidelines for contributing to this project. Read this before opening your first PR.

---

## Branch Naming

Always work on a feature branch. Never commit directly to main.

```
feature/short-description     # new features
fix/short-description          # bug fixes
chore/short-description        # maintenance, dependency updates, config changes
docs/short-description         # documentation only changes
```

Examples:
- `feature/project-listing-page`
- `feature/review-submission-form`
- `fix/db-connection-timeout`
- `chore/update-requirements`
- `docs/update-api-reference`

---

## Commit Messages

Write commit messages that describe what changed and why, not just what files were touched.

**Good:**
```
Add review submission form with rating fields
Fix database connection closing after each request
Update requirements.txt with google-cloud-secret-manager
```

**Bad:**
```
changes
fix stuff
update
wip
```

Keep the first line under 72 characters. If more context is needed, add a blank line and a longer description below.

---

## Pull Request Process

1. Make sure your branch is up to date with main before opening a PR:
   ```bash
   git pull origin main
   ```
2. Run flake8 locally and fix all violations before pushing:
   ```bash
   flake8 . --max-line-length=120 --exclude=.venv,__pycache__
   ```
3. Push your branch and open a PR targeting main on GitHub
4. Fill in the PR description — what does this PR do and why?
5. Link the PR to its GitHub issue using `Closes #issue_number` in the description — this automatically closes the issue and moves the card to Done on the project board when the PR is merged
6. Request a review from a teammate
7. Address any review comments — resolve conversations before merging
8. Once approved and all checks pass, merge

**PR description template:**
```
## What does this PR do?
Brief description of the changes.

## Why?
Context or motivation for the change.

Closes #(issue number)

## How to test?
Steps to verify the changes work locally.

## Checklist
- [ ] flake8 passes locally
- [ ] Tested locally with proxy running
- [ ] API.md updated if new routes added
- [ ] DATABASE_PLAN.md updated if schema changed
- [ ] requirements.txt updated if new packages installed
```

**Closing keywords:** `Closes`, `Fixes`, and `Resolves` all work. Use `Closes #5` to close a single issue or `Closes #5, Closes #8` to close multiple.

---

## Code Review Guidelines

**As a reviewer:**
- Review within 24 hours when possible, sooner when a deadline is close
- Be specific in feedback — point to the exact line and explain why
- Distinguish between blocking issues and suggestions
- Approve once you're satisfied — don't leave PRs hanging

**As the author:**
- Don't take feedback personally — it's about the code, not you
- Respond to every comment, even if just to acknowledge it
- If you disagree with feedback, explain why — don't just ignore it
- Resolve conversations after addressing them

---

## Code Style

- Follow PEP 8
- Max line length: 120 characters
- Docstrings on all functions — capitalized, period at end
- Inline comments lowercase
- Use `# noqa: F401` for intentionally unused imports, clean up when import is used
- Keep functions focused on one thing
- Comment non-obvious logic — explain why, not just what

---

## What to Update When You Add Something

| If you... | Update... |
|-----------|-----------|
| Add a new route | `API.md` |
| Add or change a table | `DATABASE_PLAN.md` + write a migration file |
| Install a new package | `requirements.txt` via `pip freeze` |
| Make a significant architectural decision | `DECISIONS.md` |
| Change the dev setup process | `DAILY_DEVELOPMENT.md` or `README.md` |

---

## Questions

Post in Discord first. If it's a decision that affects the whole team, bring it up in the weekly sync.
