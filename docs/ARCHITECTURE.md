\# GAGF Kernel MVP Architecture



\## Overview



The GAGF Kernel MVP is a local governance decision engine that transforms raw events into adaptive state snapshots, evaluates those snapshots against a versioned policy, and records governance decisions for auditability.



\## Architecture Layers



```text

Browser

&#x20;  ↓

Governance Console

&#x20;  ↓

FastAPI API Layer

&#x20;  ↓

Service Layer

&#x20;  ↓

Ledger Layer

&#x20;  ↓

SQLite

