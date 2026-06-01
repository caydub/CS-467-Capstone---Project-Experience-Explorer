# AI Use

**OSU Capstone Explorer — CS 467 Spring 2026**
Caleb Richter, Henry Thong, Benjamin Joseph

This document summarizes how each team member used AI tools throughout the project. Per course policy, any AI interaction that saved more than 30 minutes of work was logged with a transcript link in the full citation log.

**Full citation log (with transcripts):** https://docs.google.com/document/d/1FZg9rM7udrbKyMMLoEK2XpbhsV5j2OZIP4M7LDGEgY0/edit?usp=sharing

---

## Policy

The team followed the CS 467 GenAI policy throughout the project:

- Any AI interaction saving 30+ minutes was cited with a transcript link
- All AI-generated text submitted in assignments was rewritten in the student's own words before submission
- All AI-generated code was tested, understood, and verified by the student before committing
- Design decisions were made or confirmed by the student through active discussion — AI did not make decisions unilaterally

---

## Summary

| Team Member | Tool(s) Used | Estimated Hours Saved | Primary Use Areas |
|-------------|-------------|----------------------|-------------------|
| Caleb Richter | Claude Code (Anthropic) — Sonnet 4.6 | 75–111 hours | Infrastructure, auth, backend features, UI, archive |
| Henry Thong | ChatGPT, Microsoft Copilot | 5–8 hours | Web scraper, term dropdown |
| Benjamin Joseph | ChatGPT (OpenAI) | 16–20 hours | Templates, CSS, review forms, comments, sorting |

---

## Caleb Richter

**Tool:** Claude Code (Anthropic) — Claude Sonnet 4.6

Caleb used Claude Code in the terminal throughout all three progress report periods and the final sprint. The general workflow was sharing project files directly with Claude Code, specifying what to build, reviewing and understanding every change in the browser or by reading the code, and committing only after confirming behavior locally.

**Project Plan (PR0)**
Used Claude to scope the project, select the technology stack, define MVP vs. extended requirements, and generate the first draft of the project plan document. All text was rewritten by Caleb before submission. Estimated 4–6 hours saved.

**PR1 — Database, Routes, Scraper, Docs**
Used Claude to finalize the database schema (identifying issues with Henry's initial DDL), add insert logic to the scraper, replace hardcoded placeholder data in Flask routes with live SQL queries, fix template field name mismatches, and write the initial documentation suite. Estimated 8–12 hours saved.

**PR2 — Auth, Pseudonyms, Code Reviews, Tests**
Used Claude to implement the ONID/CAS authentication flow (login, logout, callback), the pseudonym generation system (adjective + noun + number, SHA-256 ONID hashing), and the login_required decorator. Also used Claude alongside the GitHub CLI to conduct code reviews on Henry's and Ben's PRs, and to build the initial pytest suite covering route smoke tests and auth helper functions. Estimated 10–16 hours saved.

**PR3 — Filters, Voting, UI Overhaul**
Used Claude to build the filter and sort system (HAVING clause approach, parse_rating_filter helper, all rating dimensions), helpfulness voting with toggle behavior, and a full UI overhaul covering animated rating bars, project thumbnail images, 10-per-page pagination, structured description rendering with BeautifulSoup, sticky navbar, avatar badges, relative timestamps, and a broad set of visual improvements. All design decisions — color thresholds, avatar style, vote button layout, thumbnail crop direction — were made by Caleb before implementation. Estimated 28–42 hours saved.

**Final Sprint — Feature Completion and Project Archive**
Used Claude to implement the final set of features for PR #26: difficulty→complexity rename (three-step migration due to MySQL check constraint), one review per student per project (migration + redirect logic), delete review and comment, 50-character minimum on review text, Capstone portal link, My Activity page, edit comment, mobile responsive CSS, active filter chips, delete account, site rename, custom error pages, and flash messages. Also used Claude to audit and update all documentation, fix the test suite after mock sequences became stale, and generate first drafts of all four project archive deliverables (final report, installation instructions, demo video script, and presentation slides). Estimated 25–35 hours saved.

---

## Henry Thong

**Tools:** ChatGPT, Microsoft Copilot

Henry used AI assistance on two focused tasks.

**PR1 — Web Scraper**
Used ChatGPT to learn how to navigate the OSU Capstone portal HTML structure using BeautifulSoup and requests. Asked for examples of parsing specific div classes, visiting individual project pages, filtering by text in parent elements, and debugging when the title selector returned nothing. All generated code was rewritten to fit the actual portal structure and tested by comparing output against the page source. Estimated 3–5 hours saved.

**PR3 — Term Dropdown**
Used Microsoft Copilot to help implement the generate_terms() function and replace the free-text term input in the review submission form with a standardized dropdown. Reviewed and cross-referenced with existing project code before committing. Estimated 2–3 hours saved.

---

## Benjamin Joseph

**Tool:** ChatGPT (OpenAI)

Ben used ChatGPT across all three progress report periods to help structure Flask routes and Jinja2 templates, and to implement frontend features.

**PR1 — Routes, Templates, CSS**
Used ChatGPT to structure initial Flask routes and Jinja2 template inheritance, design the homepage card layout, determine which fields to display, and establish the CSS design system. All generated code was reviewed and modified before committing. Estimated ~8 hours saved.

**PR2 — Review Forms and Display Templates**
Used ChatGPT to help build the review submission form frontend (quantitative rating fields, qualitative feedback, validation feedback, login prompt) and the review display templates (pseudonym, term, ratings, review text). Also used it to work through Code Review #1 feedback revisions. Estimated 2–4 hours saved.

**PR3 — Comments, Sorting, UI**
Used ChatGPT to implement the comments feature (display beneath reviews, authenticated submission, input validation, database query updates) and the project sorting controls (alphabetical, most reviews, highest ratings). Also used for debugging SQL query formatting and template updates during development. Estimated 8–10 hours saved.

---

## Notes

- Caleb's use of Claude Code was session-based and involved sharing actual project files rather than copy-pasting snippets. All decisions about architecture, feature scope, and behavior were made through active discussion rather than delegated to the AI.
- Henry and Ben's use of ChatGPT and Copilot was primarily for implementation support and learning unfamiliar patterns, with final decisions and testing done independently.
- No AI-generated text appears verbatim in any submitted assignment. All documents were reviewed and rewritten by the submitting student.
