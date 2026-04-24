# Project Experience Explorer

**CS 467 Spring 2026** — Caleb Richter, Henry Thong, Benjamin Joseph

A web app for OSU students to browse and submit anonymous reviews of capstone projects. Think Rate My Professor but for the OSU Capstone portal — giving future students honest peer feedback on project complexity, time commitment, and overall experience.

**Live app:** https://project-experience-explorer.uc.r.appspot.com

---

## Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| Framework | Flask |
| Templates | Jinja2 |
| Database | MySQL via Google Cloud SQL |
| Hosting | Google App Engine |
| Auth | ONID / CAS (bonus feature) |
| CI/CD | GitHub Actions |

---

## Quick Start

```bash
# 1. clone and install dependencies
git clone https://github.com/caydub/CS-467-Capstone---Project-Experience-Explorer.git
cd CS-467-Capstone---Project-Experience-Explorer
pip install -r requirements.txt

# 2. start the cloud sql proxy (separate terminal tab, keep running)
./cloud-sql-proxy project-experience-explorer:us-central1:project-experience-explorer-db

# 3. run the app
python main.py
```

Visit http://127.0.0.1:8080

For full setup instructions including venv, .env, and proxy download see [docs/DAILY_DEVELOPMENT.md](docs/DAILY_DEVELOPMENT.md).

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | PR process, code review, commit conventions |
| [docs/DAILY_DEVELOPMENT.md](docs/DAILY_DEVELOPMENT.md) | Local setup, common commands, troubleshooting |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Architectural and product decisions log |
| [docs/API.md](docs/API.md) | Flask routes reference |
| [docs/DATABASE_PLAN.md](docs/DATABASE_PLAN.md) | Schema design and migration strategy |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment process and GCP config |
| [docs/TESTING.md](docs/TESTING.md) | Testing approach (in progress) |
| [docs/SCRAPING.md](docs/SCRAPING.md) | Capstone portal scraping (in progress) |

---

## Contributing

Always work on a feature branch. Open a PR targeting main. One approval required. flake8 must pass.

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for full details.

---

## Project Status

| Week | Status |
|------|--------|
| Week 1 | Infrastructure initialized — GCP, Cloud SQL, App Engine, GitHub CI/CD. Project plan submitted. |
| Week 2 | Schema finalized and deployed to Cloud SQL. 28 CS467 projects scraped and seeded. Flask routes wired to database. Live app showing real project data. PR1 submitted. |
| Week 3 | — |
| Week 4 | — |
| Week 5 | — |
| Week 6 | — |
| Week 7 | — |
| Week 8 | — |
| Week 9 | — |
| Week 10 | Final demo and archive |

---

## Team

| Name | Focus | Timezone |
|------|-------|----------|
| Caleb Richter | GCP infrastructure, auth, filtering | CST |
| Henry Thong | Database schema, review backend, comments | PST |
| Benjamin Joseph | Frontend templates, UI, demo video | CST |

**Communication:** Discord