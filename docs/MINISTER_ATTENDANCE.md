# Minister Attendance Tracking - Implementation Guide

## Overview

This module implements AI-powered tracking of minister attendance in parliamentary minutes. It follows the spec-driven development approach to compute whether a specific minister was present in each minute containing at least one "vote nominatif" (nominal vote).

## Architecture

### Domain Layer

**Entity: `MinisterAttendance`**
- Location: `backend/domain/entities/minister_attendance.py`
- Represents a minister's attendance record for a specific minute
- Attributes:
  - `minister_id`: Member ID from database
  - `minute_ref`: Minute reference (e.g., "0072")
  - `legislature`: Legislature number
  - `present`: Boolean - whether minister was found in attendance
  - `confidence_score`: AI confidence (0.0 to 1.0)
  - `context`: Optional context string (e.g., "Vote 3")

**Repository Interface: `IMinisterAttendanceRepository`**
- Location: `backend/domain/repositories/minister_attendance_repository.py`
- Methods:
  - `save()`: Save single attendance record
  - `save_batch()`: Save multiple records
  - `find_by_minute()`: Get all ministers for a minute
  - `find_by_minister()`: Get all minutes for a minister
  - `delete_by_minute()`: Delete records for re-processing
  - `get_attendance_summary()`: Statistics (total, present, absent, rate)

### Infrastructure Layer

**Repository Implementation: `PostgreSQLMinisterAttendanceRepository`**
- Location: `backend/infrastructure/repositories/minister_attendance_repository.py`
- PostgreSQL implementation with:
  - Batch insert with conflict handling (ON CONFLICT DO UPDATE)
  - Efficient queries with proper indexing
  - Summary statistics with aggregation

**Parser: `LLMMinisterAttendanceParser`**
- Location: `backend/infrastructure/parsers/llm_minister_attendance_parser.py`
- Extracts minister presence using LLM
- Features:
  - Detects vote nominatif markers
  - Returns `None` for minutes without votes
  - Provides confidence scores
  - Fuzzy name matching to database

**Database Schema**
- Location: `db/schema.sql`
- Table: `minister_attendance`
  - Primary key: `id`
  - Unique constraint: `(minister_id, minute_ref, legislature)`
  - Foreign keys: `minister_id` → `members`, `minute_ref` → `minutes`
  - Indexes: On minister, minute, and present columns

### Job Script

**Job: `compute_minister_attendance_job.py`**
- Location: `backend/compute_minister_attendance_job.py`

**Usage:**

```bash
# Process single minute
MINISTER_NAME="Alexia Bertrand" MINUTE_REF=0072 LEGISLATURE=56 \
    python compute_minister_attendance_job.py

# Process all minutes
MINISTER_NAME="Alexia Bertrand" LEGISLATURE=56 \
    python compute_minister_attendance_job.py

# Reprocess existing records
MINISTER_NAME="Alexia Bertrand" LEGISLATURE=56 REPROCESS=true \
    python compute_minister_attendance_job.py
```

**Environment Variables:**
- `MINISTER_NAME` (required): Full name of minister
- `LEGISLATURE` (required): Legislature number (e.g., 56)
- `MINUTE_REF` (optional): Process single minute
- `REPROCESS` (optional): Reprocess already computed attendance
- `OPENAI_API_KEY` or Azure credentials: For LLM access

## Workflow

1. **Load cleaned text**: Retrieves pre-filtered minute text (votes only)
2. **Check vote nominatif**: Skips minutes without nominal votes
3. **LLM extraction**: AI checks if minister name appears in attendance
4. **Name matching**: Fuzzy match minister name to database ID
5. **Save to database**: Store attendance record with confidence
6. **Generate summary**: Calculate attendance statistics

## Key Features

### Spec-Driven Design
- Only processes minutes with vote nominatif (per spec)
- Returns `None` for non-applicable minutes
- Provides clear attendance status (present/absent)
- Includes confidence scores for validation

### Vibe Engineering
- Clear emoji-based logging (🤖 🏛️ ✅ ❌ ⚠️)
- Progress indicators for batch processing
- Detailed summaries with statistics
- Helpful error messages

### Exception Handling
- Skips minutes without vote nominatif (not counted as failures)
- Handles LLM connection errors gracefully
- Provides rate limit warnings
- Transaction-safe database operations

## Testing

**Location:** `backend/tests/test_minister_attendance.py`

Tests include:
- Entity validation (required fields, constraints)
- Confidence score handling
- Vote nominatif detection
- Repository operations (skipped until database setup)
- Parser functionality (skipped until LLM setup)

Run tests:
```bash
cd backend
pytest tests/test_minister_attendance.py -v
```

## Example Output

```
🏛️  COMPUTE MINISTER ATTENDANCE JOB
Minister: Alexia Bertrand
Legislature: 56
Reprocess: False

🔧 Initializing LLM client...
✅ LLM client created successfully
   Available models: gpt-4-turbo-preview, gpt-4, gpt-4-32k

================================================================================
Processing minute: 0072 for minister: Alexia Bertrand (Legislature 56)
================================================================================

📖 Loading cleaned text...
✅ Loaded 49120 characters of cleaned text
🤖 Parsing minister attendance for 0072 (dry_run=False)
✅ LLM result: present=True, confidence=0.95
  ✓ 'Alexia Bertrand' → Member 07683 (Match: 100%)
💾 Saved minister attendance: present=True, confidence=0.95

================================================================================
📊 RESULT FOR MINUTE 0072
================================================================================
Minister: Alexia Bertrand
Present: True
Confidence: 0.95
Context: Found in Vote 3 attendance list
================================================================================

📊 ATTENDANCE SUMMARY FOR Alexia Bertrand
================================================================================
Total minutes with votes: 44
Present: 38
Absent: 6
Attendance rate: 86.36%
================================================================================
```

## Database Queries

### Get attendance for a minister
```sql
SELECT minute_ref, present, confidence_score, context
FROM minister_attendance
WHERE minister_id = '07683' AND legislature = 56
ORDER BY minute_ref;
```

### Get attendance summary
```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN present THEN 1 ELSE 0 END) as present_count,
    ROUND(AVG(CASE WHEN present THEN 1.0 ELSE 0.0 END) * 100, 2) as rate
FROM minister_attendance
WHERE minister_id = '07683' AND legislature = 56;
```

### Get ministers present in a specific minute
```sql
SELECT m.full_name, ma.confidence_score, ma.context
FROM minister_attendance ma
JOIN members m ON ma.minister_id = m.member_id
WHERE ma.minute_ref = '0072' AND ma.legislature = 56 AND ma.present = true;
```

## Next Steps

1. **Run initial processing**: Process all minutes for a minister
2. **Validate results**: Manually check a sample of records
3. **Adjust prompts**: Fine-tune LLM prompt if needed
4. **Add API endpoints**: Expose attendance data via REST API
5. **Create dashboard**: Visualize attendance rates and trends
6. **Batch processing**: Process multiple ministers in parallel
7. **Historical analysis**: Compare attendance across legislatures

## Notes

- Only minutes with vote nominatif are processed (per spec)
- Skipped minutes are not counted in attendance statistics
- Confidence scores help identify low-quality extractions
- Name matching uses fuzzy logic for robustness
- The system is idempotent (can reprocess with REPROCESS=true)
