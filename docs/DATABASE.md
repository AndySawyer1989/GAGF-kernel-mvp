\# GAGF Kernel MVP Database



\## Overview



The GAGF Kernel MVP uses SQLite as its local persistence layer.



The database stores immutable governance evidence and Kernel decisions.



Database file:



```text

gagf.db

```



\---



\# Tables



\## gagf\_state\_snapshots



Stores normalized Adaptive State Snapshots.



Fields



\- snapshot\_id

\- tenant\_id

\- work\_item\_id

\- status

\- adaptive\_state\_json

\- evidence\_confidence\_json

\- timestamp\_quality\_distribution\_json

\- evidence\_json

\- normalization\_applied\_json

\- created\_at



Purpose



Represents the complete governance state at a single point in time.



\---



\## gagf\_decision\_records



Stores Kernel arbitration decisions.



Fields



\- decision\_id

\- snapshot\_id

\- kernel\_decision

\- selected\_strategy

\- reason\_json

\- decision\_meta\_json

\- evidence\_json

\- created\_at



Purpose



Provides a complete audit trail of every governance decision.



\---



\# Relationships



```text

Raw Events

&#x20;    │

&#x20;    ▼

Adaptive Snapshot

&#x20;    │

&#x20;    ▼

Snapshot Ledger

&#x20;    │

&#x20;    ▼

SQLite

&#x20;    │

&#x20;    ▼

Decision Ledger

&#x20;    │

&#x20;    ▼

Kernel Decision

```



Each decision references the snapshot that produced it.



\---



\# Design Principles



\- Immutable records

\- Replayable evidence

\- Auditability

\- Deterministic decision history

\- Local-first development

\- Simple relational storage



\---



\# Future Database Roadmap



Current



\- SQLite



Planned



\- PostgreSQL

\- Alembic migrations

\- Multi-tenant support

\- Backup/restore

\- Cloud deployment

