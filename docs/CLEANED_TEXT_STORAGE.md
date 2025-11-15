# Cleaned Text Storage Implementation

## Overview
Cleaned minute text storage following the same pattern as parliamentary minutes: metadata in PostgreSQL database, content in file storage (local or Azure based on environment).

## Architecture Pattern

### Use Case Orchestration
The `ExtractAttendanceUseCase` orchestrates the complete workflow:

1. **Retrieve HTML** from content storage
2. **Clean HTML** to plain text using `MinuteTextCleaner`
3. **Store content** in `IContentStorage` → receive storage key
4. **Compute hash** of cleaned text (SHA-256)
5. **Create entity** with all metadata
6. **Save metadata** to database via repository

### Separation of Concerns
- **Use Case**: Orchestrates storage operations and business logic
- **Repository**: Handles database metadata persistence only
- **Content Storage**: Handles file system or Azure blob storage

## Database Schema

```sql
CREATE TABLE cleaned_texts (
    id SERIAL PRIMARY KEY,
    minute_ref CHAR(4) NOT NULL UNIQUE,
    content_storage_key VARCHAR(500) NOT NULL,
    cleaning_method VARCHAR(50) NOT NULL,
    text_hash CHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (minute_ref) REFERENCES minutes(ref) ON DELETE CASCADE
);

CREATE INDEX idx_cleaned_texts_minute_ref ON cleaned_texts(minute_ref);
CREATE INDEX idx_cleaned_texts_text_hash ON cleaned_texts(text_hash);
CREATE INDEX idx_cleaned_texts_cleaning_method ON cleaned_texts(cleaning_method);
```

### Key Features
- **UNIQUE constraint** on `minute_ref` ensures one cleaned text per minute
- **Foreign key** cascade delete maintains referential integrity
- **Indexes** on frequently queried fields for performance
- **Hash tracking** enables change detection

## Domain Entity

```python
@dataclass(frozen=True)
class CleanedMinuteText:
    """Represents metadata about cleaned minute text."""
    minute_ref: str
    content_storage_key: str
    cleaning_method: str
    text_hash: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @staticmethod
    def compute_hash(text: str) -> str:
        """Compute SHA-256 hash of text content."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def create(minute_ref: str, content_storage_key: str,
               text_hash: str, cleaning_method: str) -> 'CleanedMinuteText':
        """Factory method for creating new metadata."""
        return CleanedMinuteText(
            minute_ref=minute_ref,
            content_storage_key=content_storage_key,
            text_hash=text_hash,
            cleaning_method=cleaning_method
        )
```

## Repository Interface

```python
class ICleanedTextRepository(ABC):
    """Repository interface for cleaned text metadata."""
    
    @abstractmethod
    def save_metadata(self, metadata: CleanedMinuteText) -> CleanedMinuteText:
        """Save or update metadata. Returns entity with id and timestamps."""
        pass
    
    @abstractmethod
    def find_by_minute_ref(self, minute_ref: str) -> Optional[CleanedMinuteText]:
        """Find metadata by minute reference."""
        pass
    
    @abstractmethod
    def exists(self, minute_ref: str) -> bool:
        """Check if metadata exists for minute reference."""
        pass
```

### PostgreSQL Implementation
- Uses `psycopg2` with context manager pattern
- **ON CONFLICT** handling for idempotent saves
- **RETURNING** clause to get generated id and timestamps
- Updates entity in-place with database values

## Content Storage

Content storage is environment-aware:
- **Development**: Local file system (`data/cleaned/`)
- **Production**: Azure Blob Storage

Storage interface (`IContentStorage`):
```python
storage_key = content_storage.store_content(f"cleaned/{minute_ref}", cleaned_text)
```

## Usage Example

```python
# Initialize dependencies
content_storage = LocalFileSystemStorage("./data")
cleaned_text_repo = PostgreSQLCleanedTextRepository(db_config)
minute_repo = PostgreSQLMinuteRepository(db_config)
text_cleaner = MinuteTextCleaner()

# Create use case
use_case = ExtractAttendanceUseCase(
    minute_repository=minute_repo,
    content_storage=content_storage,
    text_cleaner=text_cleaner,
    cleaned_text_repository=cleaned_text_repo
)

# Extract attendance (automatically stores cleaned text)
result = use_case.execute(
    minute_ref="0001",
    legislature=56
)
```

## Idempotency

The implementation is idempotent:
- **Database**: `ON CONFLICT (minute_ref) DO UPDATE` ensures reprocessing updates existing records
- **Content Storage**: Overwriting same reference updates content
- **Hash Tracking**: Detects content changes between runs

Reprocessing the same minute:
1. Retrieves fresh HTML
2. Cleans it again
3. Stores new cleaned text (overwrites)
4. Updates hash and timestamp in database

## Testing

### Entity Tests (`test_cleaned_text.py`)
- Validation rules
- Factory method
- Hash computation (deterministic, unique)

### Repository Tests (`test_cleaned_text_repository.py`)
- Database save/update operations
- Query by minute reference
- Existence checks
- Uses mocks for `psycopg2`

All tests passing: **13/13** ✓

## Benefits

1. **Separation of Storage**: Large text files don't bloat database
2. **Environment Flexibility**: Same code works locally and in production
3. **Traceability**: Hash enables change detection
4. **Clean Architecture**: Use case orchestrates, repository handles persistence
5. **Idempotent Operations**: Safe to rerun synchronization
6. **Referential Integrity**: Cascade delete maintains consistency

## Related Files

- Entity: `backend/domain/entities/cleaned_minute_text.py`
- Repository Interface: `backend/domain/repositories/cleaned_text_repository.py`
- PostgreSQL Implementation: `backend/infrastructure/repositories/cleaned_text_repository.py`
- Use Case: `backend/application/extract_attendance_use_case.py`
- Schema: `db/schema.sql`
- Tests: `backend/tests/test_cleaned_text.py`, `backend/tests/test_cleaned_text_repository.py`
