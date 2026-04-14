# Deployment

**Project Experience Explorer — CS 467 Spring 2026**

---

## Overview

The app is deployed to Google App Engine. Deployment is handled automatically by GitHub Actions on every merge to main. Manual deployment is available as a fallback.

**Live URL:** https://project-experience-explorer.uc.r.appspot.com

---

## Automatic Deployment (normal workflow)

Every merge to main triggers the deploy workflow in `.github/workflows/deploy.yml`:

1. GitHub Actions checks out the code
2. Authenticates with GCP using the `GCP_SA_KEY` secret
3. Runs `gcloud app deploy --quiet`
4. App is live within ~2 minutes

Check the Actions tab on GitHub to monitor deploy status or debug failures.

---

## Manual Deployment (fallback)

If you need to deploy manually:

```bash
# make sure you're in the project root (where app.yaml is)
gcloud app deploy

# open the live app in browser
gcloud app browse
```

Make sure your gcloud CLI is pointed at the right project first:

```bash
gcloud config list
# should show project: project-experience-explorer and your OSU account
```

---

## GCP Project Info

| Property | Value |
|----------|-------|
| Project ID | project-experience-explorer |
| Project number | 63516489976 |
| Region | us-central1 |
| App Engine service | default |
| Cloud SQL instance | project-experience-explorer-db |
| Database | project_explorer_db |
| DB user | flask_user |
| Secret name | db_flask_user_password |

---

## Environment Configuration

**Local development:**
- Database password stored in `.env` as `DB_PASSWORD`
- Flask reads it via `python-dotenv`
- `.env` is never committed to the repo

**App Engine (production):**
- Database password stored in GCP Secret Manager as `db_flask_user_password`
- Flask reads it at runtime via `google-cloud-secret-manager`
- No environment variables needed in `app.yaml`

---

## Schema Migrations on Deploy

When a deploy includes database schema changes:

1. Apply the migration to Cloud SQL **before** deploying the new app version
2. Open Cloud SQL Studio in the GCP Console
3. Connect as `flask_user`
4. Run the migration SQL
5. Confirm the change
6. Then deploy the new app version

> Never deploy code that depends on a schema change before applying the migration — the app will break.

---

## Monitoring and Logs

**Stream live logs:**
```bash
gcloud app logs tail -s default
```

**View logs in GCP Console:**
App Engine → Services → default → Logs

**Check deployed versions:**
App Engine → Versions

---

## Troubleshooting Deploys

**Deploy fails with permissions error:**
- Check the GitHub Actions log for the specific error
- Verify the `GCP_SA_KEY` secret is still valid in GitHub repo settings
- Check the `github-actions-deploy` service account has the right roles in GCP IAM

**App deploys but crashes on startup:**
- Check App Engine logs immediately after deploy
- Common causes: missing secret, bad Cloud SQL connection string, import error

**Changes not showing after deploy:**
- Hard refresh the browser (Cmd+Shift+R / Ctrl+Shift+R)
- Check GitHub Actions to confirm the deploy actually ran
- Check App Engine → Versions to confirm the new version is receiving traffic

**Rolled back accidentally to old version:**
- App Engine → Versions → click the latest version → Migrate Traffic

---

## Rolling Back

If a bad deploy goes out:

1. Go to GCP Console → App Engine → Versions
2. Find the last working version
3. Click the three dots → Migrate Traffic
4. Traffic shifts back to the old version immediately

Then fix the issue on a branch, open a PR, and redeploy through the normal process.
