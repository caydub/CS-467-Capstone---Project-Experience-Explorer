# Daily Development Reference

**Project Experience Explorer — CS 467 Spring 2026**

Quick reference for common development tasks and things that will bite you if you forget.

---

## Starting Up Locally

Every time you sit down to work, do these in order:

**1. Start the Cloud SQL Auth Proxy in a separate terminal tab and leave it running**

The proxy creates a secure tunnel between your machine and the Cloud SQL database on Google's servers. Your Flask app can't reach the database without it. If you skip this step you'll get a confusing connection error.

```bash
# Mac/Linux:
./cloud-sql-proxy project-experience-explorer:us-central1:project-experience-explorer-db

# Windows:
.\cloud-sql-proxy.exe project-experience-explorer:us-central1:project-experience-explorer-db
```

You should see: `The proxy has started successfully and is ready for new connections!`

Leave this terminal tab open the whole time you're working. If you close it, your database connection dies.

**2. In a second terminal tab, activate your venv and run the app**

Check that `(.venv)` appears at the start of your terminal prompt. If it doesn't, activate it:

```bash
# Mac/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

Then run the app:

```bash
python main.py
```

Visit http://127.0.0.1:8080 to confirm it's running.

---

## Daily Catches

**Development**
- Always start the proxy before running the app — database connection will fail without it
- Check for `(.venv)` in your terminal prompt every new session — venv doesn't persist between sessions
- Run `pip freeze > requirements.txt` every time you install a new package — teammates get import errors if you forget
- Hard refresh the browser after deploying — App Engine caches aggressively, changes might not show immediately

**GCP**
- Cloud SQL costs credits even when idle — check the billing dashboard occasionally
- Always use your OSU account for GCP — never your personal Gmail

**Code**
- Remove the `/test-db` route before the final demo — don't leave debug routes in production
- Never commit `.env` — run `git status` before every commit if unsure
- `# noqa: F401` is fine for temporarily unused imports but clean them up once the import is actually used

**GitHub**
- Always work on a feature branch, never directly on main
- Run flake8 locally before pushing — saves a failed PR check

---

## Common Commands

**Run flake8 linting locally:**
```bash
flake8 . --max-line-length=120 --exclude=.venv,__pycache__
```
No output means you're clean. Violations show as `filename:line:col: error code message`.

**Install all dependencies:**
```bash
pip install -r requirements.txt
```

**Save dependencies after installing a new package:**
```bash
pip freeze > requirements.txt
```

**Check your GCP project and account:**
```bash
gcloud config list
```

**Stream live App Engine logs:**
```bash
gcloud app logs tail -s default
```

**Deploy manually (normally handled by GitHub Actions on merge to main):**
```bash
gcloud app deploy
```

---

## Git Workflow

```bash
# 1. Pull latest changes
git pull

# 2. Create a feature branch
git checkout -b your-feature-name

# 3. Do your work, then stage and commit
git add .
git commit -m "descriptive commit message"

# 4. Push your branch
git push

# 5. Open a PR on GitHub targeting main
# 6. Get a teammate to review and approve
# 7. Merge — app auto-deploys
```

**Branch naming suggestions:**
- `feature/project-listing-page`
- `feature/review-submission-form`
- `fix/db-connection-error`
- `chore/update-requirements`

---

## When Something Breaks

**App won't start locally:**
- Is `(.venv)` in your terminal prompt? If not, activate the venv.
- Run `pip install -r requirements.txt` — you might be missing a package.

**Database connection error:**
- Is the proxy running in another terminal tab?
- Does your `.env` file have `DB_PASSWORD` set correctly?

**flake8 failing on PR:**
- Run `flake8 . --max-line-length=120 --exclude=.venv,__pycache__` locally to see the violations.
- Fix them before pushing again.

**Deployed app not showing changes:**
- Hard refresh the browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows).
- Check GitHub Actions to confirm the deploy succeeded.
- Check App Engine logs: `gcloud app logs tail -s default`

**GCP permission error:**
- Make sure you're authenticated with your OSU account: `gcloud config list`
- If account is wrong: `gcloud auth login`
