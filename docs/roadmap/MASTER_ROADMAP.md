# GAGF / FIP Master Roadmap

## Portfolio

### Core Systems
- GAGF Constitutional Kernel
- FIP Diagnostic and Intervention Pipeline
- G-CDSS Simulation Engine
- ESY Adaptive Operating System and Runtime

### Active Commercial Products
- FIP Governance Diagnostics and Assessment
- FIP Adaptive Game Intelligence

### Planned Commercial Products
- FIP Simulation and Scenario Lab
- G-CDSS Knowledge Assistant
- Personal Friction Assistant
- Personal Resilience Dashboard
- Embedded FIP Enterprise API
- ESY Runtime Developer Edition
- ESY Adaptive Server and Edge OS
- ESY Gaming Runtime
- ESY Consumer Operating System

### Private and Internal Products
- GAGF Governance Console
- Constitutional Replay and Audit Workbench
- Policy Authoring and Verification Studio
- G-CDSS Research Simulation Workbench
- Product Telemetry and Experimentation Lab
- Private Strategic Analysis Environment
- ESY Private Secure Operating Environment
- ESY Research Distribution

## Current Baseline
- US-059 completed
- 574 automated tests passing
- Constitutional evidence, sequencing, partition fencing, and commit gating implemented

## Active Epics

### Core
- EPIC-CORE-ADAPTIVE-CAPACITY
- Next core pipeline user story: US-0108

### Commercial
- EPIC-DIAG-001 — Governance Diagnostics Pilot
- EPIC-GAME-001 — Adaptive Encounter Director

### ESY
- EPIC-ESY-001 — Adaptive Linux Runtime

### Private
- EPIC-AUDIT-001 — Constitutional Replay Workbench

## Capacity Allocation

Until recurring revenue:
- 70% core platform
- 20% commercial product
- 10% private tools and planning

After paid pilots:
- 60% core platform
- 30% commercial product
- 10% private tools and research

## Delivery Cadence
- Two core stories
- One bounded product story
- Repeat

## Engineering Rules
- Contract-first development
- Test-first implementation
- Focused tests before full-suite tests
- No story complete until the full suite passes
- Product-specific code may depend on stable core services
- Core services must not depend on product-specific modules
- No more than two commercial products in active implementation at once

## Immediate Sequence
1. Define US-0108 acceptance criteria
2. Implement US-0108
3. Implement the next core story
4. Begin GAME-001 game telemetry contracts
5. Continue Adaptive Capacity
6. Begin DIAG-001 commercial pilot packaging
