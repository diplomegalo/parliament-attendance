# AGENT.md – Parliament Attendance

## Mission
Create a resilient, idempotent web application to retrieve and analyze true attendance of Belgian ministers in parliament sessions. Backend in Python (clean architecture, TDD, DDD, business naming). Frontend should use SSG (suggest: Astro, Next.js SSG, or Hugo) and update monthly. Use devcontainer for development environment.

## Main Scenario
1. **Batch Scraping:** Monthly job scrapes parliamentary minutes (provisoire/definitive). Only "provisoire" versions are recalculated/replaced; "definitive" are immutable.
2. **Storage:** Save minutes in convenient, scalable storage (suggest: S3, Azure Blob, or local filesystem; configurable).
3. **Parsing:** Extract ministers' names and votes from minutes. Register votes per session.
4. **Attendance Calculation:** Count each minister's presence/absence. Calculate % attendance.
5. **KPI Generation:** Output list of ministers, attendance %, and vote topics for web app.
6. **Web App:** SSG frontend displays KPIs, minister selection, and vote details.

## Architecture & Conventions
- **Backend:** Python, clean architecture, TDD, DDD, business-oriented naming. All logic in domain/service layers. Tests required for all business logic.
- **Frontend:** SSG framework (Astro, Next.js SSG, Hugo, etc.). Minimal runtime JS. Monthly rebuild.
- **Dev Environment:** Use devcontainer for reproducibility. Document setup in `/.devcontainer/`.
- **Dependencies:** All new dependencies must be approved before addition.
- **Documentation:** Document all modules, classes, and functions. Update AGENT.md and README.md for major changes.
- **Simplicity First:** Application code must be as simple as possible and purely functional/business-oriented. Infrastructure concerns (cron scheduling, parallelism, async processing, etc.) must NOT be part of the application code. Delegate to external tools (cron, task schedulers, orchestrators) first, or well-established libraries as fallback. Keep application code focused on business logic only.

## Integration & Data Flow
- **Batch job:** Runs monthly, triggers scraping, parsing, and DB update.
- **Storage:** Abstract storage layer; configurable backend (S3, Azure, local).
- **Database:** Use schema migration tools; avoid manual changes. Store attendance, votes, and session metadata.
- **Frontend:** Consumes precomputed KPIs and attendance data; no direct DB access.

## Testing & Validation
- **TDD:** Write tests before implementing business logic. Use domain-driven test names.
- **Resilience:** Batch must handle failures gracefully and be idempotent.
- **Efficiency:** Optimize parsing and DB operations for large/minute-heavy sessions.

## Examples
- Scraping: `python backend/sync_job.py` (monthly batch)
- Testing: `pytest backend/tests/` (all business logic)
- Devcontainer: Launch VS Code in devcontainer for consistent environment

## Agent Guidance
- Use business terms for all class/function names (e.g., `MinisterAttendanceCalculator`, `SessionVoteParser`).
- Document all new features and architectural decisions.
- Propose SSG frontend options if not specified.
- Request approval for new dependencies before adding.
- Ask for clarification if requirements or conventions are unclear.

---
For further details, consult AGENT.md, README.md, or ask for clarification.
