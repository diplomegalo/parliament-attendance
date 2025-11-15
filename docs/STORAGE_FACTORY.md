# Storage Factory - Content Segregation

## Overview

The Storage Factory provides a centralized way to create storage instances with built-in content segregation support. This allows different types of content (original minutes, cleaned text, etc.) to be stored in separate locations while maintaining a consistent interface.

## Architecture

### Local Storage
- Base path: `data/` (configurable via `LOCAL_STORAGE_PATH`)
- Content segregation: Subdirectories
  - Minutes: `data/minutes/`
  - Cleaned text: `data/cleaned/`
  - Custom: `data/{storage_name}/`

### Azure Blob Storage
- Container: `parliament` (configurable via `AZURE_STORAGE_CONTAINER`)
- Content segregation: Blob prefixes
  - Minutes: `parliament/minutes/file.html`
  - Cleaned text: `parliament/cleaned/file.html`
  - Custom: `parliament/{storage_name}/file.html`

## Usage

### Basic Usage

```python
from infrastructure.storage.storage_factory import StorageFactory

# Create storage for original minutes
minutes_storage = StorageFactory.create_minutes_storage()

# Create storage for cleaned text
cleaned_storage = StorageFactory.create_cleaned_storage()

# Create custom storage
custom_storage = StorageFactory.create_storage(storage_name='custom')
```

### Job Integration

```python
# In sync_job.py - for original minutes
content_storage = StorageFactory.create_minutes_storage()

# In extract_attendance_job.py - for cleaned text
content_storage = StorageFactory.create_cleaned_storage()

# In compute_attendance_job.py - for cleaned text
content_storage = StorageFactory.create_cleaned_storage()
```

## Configuration

### Environment Variables

```bash
# Storage type
CONTENT_STORAGE=local  # or 'azure'

# Local storage configuration
LOCAL_STORAGE_PATH=./data  # Base path for local storage

# Azure storage configuration
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER=parliament  # Container name

# Content segregation (optional)
MINUTES_STORAGE_NAME=minutes  # Default: 'minutes'
CLEANED_STORAGE_NAME=cleaned  # Default: 'cleaned'
```

### Example Configurations

#### Development (Local)
```bash
CONTENT_STORAGE=local
LOCAL_STORAGE_PATH=./data
MINUTES_STORAGE_NAME=minutes
CLEANED_STORAGE_NAME=cleaned
```

Result:
- Minutes: `./data/minutes/0001.html`
- Cleaned: `./data/cleaned/cleaned_0001.txt.html`

#### Production (Azure)
```bash
CONTENT_STORAGE=azure
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_STORAGE_CONTAINER=parliament
MINUTES_STORAGE_NAME=minutes
CLEANED_STORAGE_NAME=cleaned
```

Result:
- Minutes: `parliament/minutes/0001.html`
- Cleaned: `parliament/cleaned/cleaned_0001.txt.html`

## Factory Methods

### `create_storage(storage_name, storage_type)`

Generic factory method for creating storage instances.

**Parameters:**
- `storage_name` (optional): Subdirectory or blob prefix for segregation
- `storage_type` (optional): 'local' or 'azure' (defaults to `CONTENT_STORAGE` env var)

**Returns:** `IContentStorage` implementation

### `create_minutes_storage()`

Creates storage for original parliamentary minutes.
Uses `MINUTES_STORAGE_NAME` env var (default: 'minutes').

### `create_cleaned_storage()`

Creates storage for cleaned text content.
Uses `CLEANED_STORAGE_NAME` env var (default: 'cleaned').

## Benefits

1. **Clear Segregation**: Different content types are stored in separate locations
2. **Consistent Interface**: All storage types implement `IContentStorage`
3. **Environment-Based**: Easy switching between local and Azure storage
4. **Configurable**: Storage names can be customized via environment variables
5. **Extensible**: Easy to add new content types (e.g., 'votes', 'attendance')
6. **Backward Compatible**: Existing code continues to work with defaults

## Migration Guide

### Before (Old Pattern)

```python
# Old way with hardcoded paths
from infrastructure.storage.local_file_storage import LocalFileSystemStorage

storage = LocalFileSystemStorage('./data/minutes')
```

### After (New Pattern)

```python
# New way with factory
from infrastructure.storage.storage_factory import StorageFactory

storage = StorageFactory.create_minutes_storage()
```

## Implementation Details

### LocalFileSystemStorage Changes

```python
def __init__(self, base_path: str = None, storage_name: str = None):
    # base_path defaults to workspace/data
    # storage_name creates subdirectory (default: 'minutes')
    # Final path: {base_path}/{storage_name}/
```

### AzureBlobStorage Changes

```python
def __init__(self, connection_string, container_name, storage_name=None):
    # storage_name adds blob prefix (optional)
    # Blob path: {storage_name}/{filename} or just {filename}
```

## Testing

Run the storage factory test:

```bash
python -c "
from infrastructure.storage.storage_factory import StorageFactory

# Test minutes storage
minutes = StorageFactory.create_minutes_storage()
print(f'Minutes: {minutes.base_path}')

# Test cleaned storage
cleaned = StorageFactory.create_cleaned_storage()
print(f'Cleaned: {cleaned.base_path}')
"
```

## Related Files

- `infrastructure/storage/storage_factory.py` - Factory implementation
- `infrastructure/storage/local_file_storage.py` - Local storage with subdirectories
- `infrastructure/storage/azure_blob_storage.py` - Azure storage with blob prefixes
- `sync_job.py` - Uses minutes storage
- `extract_attendance_job.py` - Uses cleaned storage
- `compute_attendance_job.py` - Uses cleaned storage
