# AGENT.md – Parliament Attendance

## Mission
Create a resilient, idempotent web application to retrieve and analyze true attendance of Belgian ministers in parliament sessions. Backend in Python (clean architecture, TDD, DDD, business naming). Frontend should use SSG (suggest: Astro, Next.js SSG, or Hugo) and update monthly. Use devcontainer for development environment.

## Main Scenario
1. **Member List Prerequisite:** Before processing minutes, check if member list exists for target legislature. If not, automatically scrape and save member list from parliament URL.
2. **Member List Scraping:** Scrape and maintain official member list per legislature from parliament URL. Members are unique per legislature and list is static during legislature period.
3. **Batch Scraping:** Monthly job scrapes parliamentary minutes (provisoire/definitive). Only "provisoire" versions are recalculated/replaced; "definitive" are immutable.
4. **Storage:** Save minutes in convenient, scalable storage (suggest: S3, Azure Blob, or local filesystem; configurable).
5. **Parsing:** Extract member names and votes from minutes. Match against official member list. Register votes per session.
6. **Minister Identification:** Ministers are members with special status/role. Associate minister status to members.
7. **Attendance Calculation:** Count each member's (especially ministers') presence/absence. Calculate % attendance.
8. **KPI Generation:** Output list of members/ministers, attendance %, and vote topics for web app.
9. **Web App:** SSG frontend displays KPIs, member/minister selection, and vote details.

## Architecture & Conventions
- **Backend:** Python, clean architecture, TDD, DDD, business-oriented naming. All logic in domain/service layers. Tests required for all business logic.
- **Frontend:** SSG framework (Astro, Next.js SSG, Hugo, etc.). Minimal runtime JS. Monthly rebuild.
- **Dev Environment:** Use devcontainer for reproducibility. Document setup in `/.devcontainer/`.
- **Dependencies:** All new dependencies must be approved before addition.
- **Documentation:** Document all modules, classes, and functions. Update AGENT.md and README.md for major changes.
- **Simplicity First:** Application code must be as simple as possible and purely functional/business-oriented. Infrastructure concerns (cron scheduling, parallelism, async processing, etc.) must NOT be part of the application code. Delegate to external tools (cron, task schedulers, orchestrators) first, or well-established libraries as fallback. Keep application code focused on business logic only.

### Devcontainer Configuration
**Responsibilities:**
- Keep `.devcontainer/devcontainer.json` up-to-date with project needs (Python, Docker, PostgreSQL, etc.)
- Ensure all required VS Code extensions are listed and relevant settings are configured
- Maintain correct `dockerComposeFile` and service mappings for backend/frontend/database
- Forward necessary ports (e.g., 5432 for PostgreSQL) and document their use
- Add or update VS Code settings for Python linting, formatting, and environment management
- Ensure `postCreateCommand` installs all backend dependencies reliably

**Conventions:**
- Use only approved features and extensions
- Prefer official or well-supported devcontainer features
- Keep configuration minimal but sufficient for all workflows (backend, database, testing)
- Use business-oriented naming for services and folders
- Document all changes and rationale in AGENT.md

## Integration & Data Flow
- **Batch job:** Runs monthly, triggers scraping, parsing, and DB update.
- **Storage:** Abstract storage layer; configurable backend (S3, Azure, local).
- **Database:** Use schema migration tools; avoid manual changes. Store attendance, votes, and session metadata.
- **Frontend:** Consumes precomputed KPIs and attendance data; no direct DB access.

## Implementation Details

### Content Storage Architecture (Implemented)
**Decision:** Separate large HTML content from database to improve scalability and maintainability.

**Implementation:**
- **Domain Layer:** `IContentStorage` interface defines storage contract (store_content, retrieve_content, exists)
- **Infrastructure Implementations:**
  - `LocalFileSystemStorage`: Stores HTML files in `./data/minutes/` directory (development)
  - `AzureBlobStorage`: Stores in Azure Blob Storage container (production)
- **Entity Updates:** `ParliamentaryMinute` uses `content_storage_key` instead of `full_text_content`
- **Configuration:** Environment variable `CONTENT_STORAGE` selects provider ('local' or 'azure')
- **Database Schema:** Store only metadata + `content_storage_key` reference; remove `minutes_text` table

**Rationale:**
- Database optimized for metadata queries, not large text storage
- Easy to switch between local development and cloud production
- Follows Clean Architecture: domain defines interface, infrastructure provides implementations
- Content can be cached/CDN-served independently from database

**Next Steps:**
1. Database migration: Add `content_storage_key` column, drop `minutes_text` table
2. Add `azure-storage-blob` to `requirements.txt`
3. Test with real scraping data

### Clean Architecture Layers
**Domain Layer** (`backend/domain/`):
- Pure business entities: `SessionReference`, `SessionMetadata`, `ParliamentaryMinute`
- Repository interfaces (ports): `ISessionMetadataRepository`, `IMinuteRepository`, `IMinuteContentRetriever`, `IContentStorage`, `IMemberRepository`, `IMemberScraper`
- No external dependencies, only Python standard library

**Application Layer** (`backend/application/`):
- Use cases orchestrate business workflows:
  - `SynchronizeMembersUseCase`: Ensures member data exists for legislature (prerequisite check)
  - `SynchronizeMinutesUseCase`: Retrieves and stores parliamentary minutes for a legislature
- Depend only on domain interfaces, not concrete implementations
- Handle business rules like "don't overwrite definitive minutes" and "members must exist before processing minutes"

**Infrastructure Layer** (`backend/infrastructure/`):
- Concrete implementations (adapters): `ParliamentarySessionScraper`, `PostgresMinuteRepository`, `PostgresMemberRepository`, `ChamberMemberScraper`, `LocalFileSystemStorage`, `AzureBlobStorage`
- Session scraper accepts legislature parameter and dynamically constructs URLs
- External dependencies: `psycopg2`, `beautifulsoup4`, `requests`, `azure-storage-blob`
- Main entry point (`sync_job.py`) wires dependencies together and executes two-step process:
  1. Member synchronization (prerequisite)
  2. Minute synchronization (with legislature parameter)
  3. Passes legislature to web scraper for URL construction

### Testing Strategy
- **Domain Tests** (`test_domain_entities.py`): Pure unit tests, no mocks needed
- **Use Case Tests** (`test_use_case.py`): Mock all infrastructure dependencies
- **Infrastructure Tests** (`test_infrastructure.py`): Integration tests with mock HTML responses
- **Storage Tests** (`test_content_storage.py`): File system operations with `tempfile` for isolation

### Current Focus: Legislature 56
- **Time Period:** 2024-present (current legislature)
- **Document Types:** Provisoire (provisional) and Définitif (definitive) minutes
- **Source:** Belgian Federal Parliament website
- **Update Strategy:** Provisional minutes can be updated/replaced; definitive are immutable
- **Multi-Legislature Support:** Web scraper accepts legislature parameter and constructs URLs dynamically
- **URL Template:** `https://www.lachambre.be/kvvcr/showpage.cfm?section=/cricra&language=fr&cfm=dcricra.cfm?type=plen&cricra=CRI&count=all&legislat={legislature}`

### Members & Ministers Management
**Domain Rules:**
- **Prerequisite Check:** Member list must exist for a legislature before processing its minutes
- **Auto-Scraping:** If member list doesn't exist, system automatically scrapes and saves it
- **Members:** Parliamentary members list retrieved from parliament URL and scrapped
- **Legislature Association:** Members are associated to a legislature (same as minutes)
- **Uniqueness:** A member is unique per legislature (cannot be member twice for same legislature)
- **Minister Status:** A minister is a member with special status/role attribute
- **Static List:** Member list doesn't change during a legislature (only updated when scraped)
- **Database Schema:** Members stored with `member_id`, `legislature`, `full_name`, `party`, `constituency`
- **Constraint:** `UNIQUE(member_id, legislature)` ensures no duplicates

**Implementation (Updated):**
- **Two Use Cases:**
  - `SynchronizeMembersUseCase`: Checks if members exist; scrapes if missing; saves to database
  - `SynchronizeMinutesUseCase`: Processes minutes for a specific legislature
- **Execution Flow:**
  1. `sync_job.py` reads `LEGISLATURE` environment variable (default: 56)
  2. Execute `SynchronizeMembersUseCase` first (prerequisite)
  3. If members exist → skip scraping, log count
  4. If members missing → scrape from web, save to database
  5. Execute `SynchronizeMinutesUseCase` with legislature parameter
- **Infrastructure Components:**
  - `PostgresMemberRepository`: Handles member CRUD operations
  - `ChamberMemberScraper`: Scrapes member list from parliament website
- **Database Tables:**
  - `members`: Stores member data with `UNIQUE(member_id, legislature)` constraint
  - `minutes`: Stores minute metadata with `legislature` column
- **Minister Identification:** Happens through member role/status (to be implemented)

**Environment Variables:**
- `LEGISLATURE=56` (default): Legislature number to process

## Testing & Validation
- **TDD:** Write tests before implementing business logic. Use domain-driven test names.
- **Resilience:** Batch must handle failures gracefully and be idempotent.
- **Efficiency:** Optimize parsing and DB operations for large/minute-heavy sessions.

## Examples
- **Scraping (default legislature 56):** `python backend/sync_job.py`
- **Scraping (custom legislature):** `LEGISLATURE=57 python backend/sync_job.py`
- **Testing:** `cd backend && python -m unittest discover -s tests -v` (all tests)
- **Quick integration test:** `python backend/test_integration_flow.py`
- **Devcontainer:** Launch VS Code in devcontainer for consistent environment
- **Update Python dependencies:** Edit `postCreateCommand` in `.devcontainer/devcontainer.json`
- **Add VS Code extension:** List in `customizations.vscode.extensions` and request approval
- **Forward a new port:** Add to `forwardPorts` and explain its purpose

## Agent Guidance
- Use business terms for all class/function names (e.g., `MinisterAttendanceCalculator`, `SessionVoteParser`).
- Document all new features and architectural decisions in both AGENT.md and README.md.
- **Always update README.md** when implementing significant features or architectural changes.
- Propose SSG frontend options if not specified.
- Request approval for new dependencies or devcontainer features/extensions before adding.
- Ask for clarification if requirements or conventions are unclear.
- For devcontainer changes: propose improvements for efficiency, reproducibility, or developer experience.

## Project Philosophy
**This is a vibe coding project.** Development is guided by intuition, experimentation, and practical results rather than rigid planning. The architecture emerged organically through iterative refinement while maintaining clean code principles.

### Python Environment
- **Dev Container:** Uses system Python with optional venv for IDE features
- **Virtual Environment:** Optional `.venv/` for VS Code IntelliSense/autocomplete
- **Deployment:** Azure Functions manages Python environment automatically from `requirements.txt`
- **Testing:** Run tests with `python -m unittest discover -s backend/tests` (from workspace root)

---
For further details, consult AGENT.md, README.md, or ask for clarification.
