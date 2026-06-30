# GAGF Kernel MVP

> General Adaptive Governance Framework (GAGF) Kernel MVP

A local-first governance decision engine that converts raw operational events into adaptive state snapshots, evaluates those snapshots using a declarative Governance Policy Language (GPL), and records deterministic governance decisions with a complete audit trail.

---

# Current Version

**v0.1.0**

Status:

- ✅ Stable MVP
- ✅ Local Execution
- ✅ Automated Tests Passing
- ✅ Governance Console Available

---

# Features

- Adaptive State Metric Adapter
- Governance Policy Language (GPL)
- Deterministic Arbitration Engine
- Snapshot Ledger
- Decision Ledger
- SQLite Persistence
- REST API
- Governance Console
- Dashboard Service
- Automated pytest Suite

---

# Architecture

```text
Browser
     │
     ▼
Governance Console
     │
     ▼
FastAPI
     │
     ▼
Dashboard Service
     │
     ▼
Snapshot Ledger
Decision Ledger
     │
     ▼
SQLite
     │
     ▼
Kernel
     │
     ▼
Metric Adapter
```

---

# API Endpoints

| Method | Endpoint |
|---------|----------|
| GET | /health |
| POST | /snapshot |
| POST | /arbitrate |
| GET | /snapshots |
| GET | /snapshot/{id} |
| GET | /decisions |
| GET | /decision/{id} |
| GET | /dashboard |
| GET | /console |

---

# Running Locally

Create and activate the virtual environment.

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
py -m uvicorn backend.app.main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

Governance Console:

```
http://127.0.0.1:8000/console
```

---

# Testing

Run:

```bash
pytest
```

All tests should pass before committing changes.

---

# Documentation

See the `docs/` folder:

- ARCHITECTURE.md
- API.md
- DATABASE.md

---

# Roadmap

## Version 0.2

- Dashboard enhancements
- Improved Governance Console
- Charts and visualizations

## Version 0.3

- Jira integration
- GitHub integration
- CSV ingestion

## Version 1.0

- Friction Intelligence Platform (FIP)
- PostgreSQL
- Authentication
- Enterprise deployment

---

# License

Development project for research, governance engineering, and software architecture.