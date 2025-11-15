# AI-Powered Attendance Extraction

This document describes the AI-powered attendance extraction system using Large Language Models (LLMs).

## Overview

The attendance extraction process is split into two independent jobs:

1. **Text Cleaning** (`extract_attendance_job.py`): Converts HTML minutes to clean plain text
2. **AI Extraction** (`compute_attendance_job.py`): Uses LLM to extract attendance from cleaned text

This separation provides:
- **Cost efficiency**: Text cleaning is free, AI analysis costs money
- **Flexibility**: Reprocess AI extraction without re-cleaning text
- **Testability**: Test each step independently

## Architecture

### LLM Abstraction Layer

The system uses a provider-agnostic abstraction that allows switching between LLM providers without code changes:

```
Domain Layer (Interfaces)
├── ILLMClient (abstract interface)
├── LLMError (exception hierarchy)
└── Schema definitions

Infrastructure Layer (Implementations)
├── OpenAIClient (OpenAI API)
├── AzureOpenAIClient (Azure OpenAI Service)
├── AnthropicClient (Anthropic Claude - future)
└── OllamaClient (Local LLM - future)

Factory Pattern
└── LLMFactory (environment-based selection)
```

### Provider Selection

The `LLMFactory` automatically selects the LLM provider based on environment variables (in priority order):

1. **Azure OpenAI** (`AZURE_OPENAI_ENDPOINT`) - Enterprise, EU data residency
2. **Anthropic Claude** (`ANTHROPIC_API_KEY`) - Coming soon
3. **OpenAI** (`OPENAI_API_KEY`) - Recommended for getting started
4. **Ollama** (`OLLAMA_HOST`) - Free local alternative - Coming soon

To switch providers, simply update environment variables. No code changes required.

## Usage

### Prerequisites

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your LLM API key (OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT)
```

### Running the Jobs

#### 1. Text Cleaning (First Step)

```bash
# Clean all minutes for legislature 56
cd backend
LEGISLATURE=56 python extract_attendance_job.py

# Clean a specific minute
LEGISLATURE=56 MINUTE_REF=0001 python extract_attendance_job.py
```

Output:
- Cleaned text stored in `data/minutes/cleaned_XXXX.txt`
- Metadata in database (`cleaned_texts` table)
- Idempotent: Safe to re-run

#### 2. AI Extraction (Second Step)

```bash
# Extract attendance for all minutes
cd backend
LEGISLATURE=56 python compute_attendance_job.py

# Extract attendance for a specific minute
LEGISLATURE=56 MINUTE_REF=0001 python compute_attendance_job.py

# Reprocess already extracted attendance
LEGISLATURE=56 REPROCESS=true python compute_attendance_job.py
```

Output:
- Member presence records in `attendance` table (coming soon)
- Statistics: matched members, confidence scores
- Unmatched names for manual review

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | One of LLM keys | OpenAI API key | `sk-proj-xxx...` |
| `AZURE_OPENAI_ENDPOINT` | One of LLM keys | Azure OpenAI endpoint | `https://xxx.openai.azure.com/` |
| `LEGISLATURE` | Yes | Legislature number | `56` |
| `MINUTE_REF` | No | Specific minute to process | `0001` |
| `REPROCESS` | No | Reprocess existing records | `true` or `false` |
| `FUZZY_MATCH_THRESHOLD` | No | Name matching threshold (0-100) | `85` (default) |

## Fuzzy Name Matching

The system uses **RapidFuzz** (Levenshtein distance) to match member names from LLM output to database records.

### Algorithm

1. LLM extracts names from text (e.g., "M. Jean Dupont", "Dupont")
2. Fuzzy matcher tries multiple variations:
   - Full name: "Jean Dupont"
   - Last name only: "Dupont"
   - "FirstName LastName"
   - "LastName FirstName"
3. Returns best match above threshold (default: 85%)

### Confidence Scoring

Final confidence = `min(LLM confidence, fuzzy match score / 100)`

Example:
- LLM extracts "Jean Dupont" with confidence 0.95
- Fuzzy matcher finds "Jean Dupond" with 87% similarity
- Final confidence: `min(0.95, 0.87) = 0.87`

### Tuning

Adjust `FUZZY_MATCH_THRESHOLD` based on results:
- **Too low** (< 80): False positives, wrong matches
- **Too high** (> 90): False negatives, missing valid matches
- **Recommended**: 85 (good balance)

## LLM Prompt Engineering

The system uses a carefully crafted prompt for attendance extraction:

### Prompt Structure

```
1. Role definition: "You are analyzing Belgian parliamentary minutes..."
2. Task description: Extract member names, spoke status, confidence
3. Guidelines:
   - Only include MPs (not ministers or guests)
   - Conservative confidence scoring
   - Handle name variations
4. Input: Cleaned text (truncated to ~15k chars)
5. Output: JSON schema with validation
```

### JSON Schema

```json
{
  "members": [
    {
      "name": "Full name as written in text",
      "spoke": true or false,
      "confidence": 0.0 to 1.0
    }
  ]
}
```

### Temperature Setting

- **Temperature = 0.0**: Deterministic, consistent results
- Ensures reproducibility across runs

## Cost Management

### Token Usage

- **Input tokens**: ~5,000-10,000 per minute (depending on length)
- **Output tokens**: ~500-1,000 per minute
- **Total cost** (GPT-4-turbo): ~$0.01-0.03 per minute

For 72 minutes:
- Estimated cost: **$0.72 - $2.16**
- Processing time: ~5-10 minutes

### Optimization Strategies

1. **Text truncation**: Limit to 15,000 chars (~3,750 tokens)
2. **Caching**: Store LLM responses to avoid reprocessing
3. **Batch processing**: Process multiple minutes in parallel (future)
4. **Model selection**: Use `gpt-4-turbo-preview` (cheaper than `gpt-4`)
5. **Local alternative**: Use Ollama with Llama 3 (free, slower)

## Testing

### Unit Tests (Mock LLM)

```bash
# Test with mock LLM client (no API calls)
cd backend
python -m pytest tests/test_llm_extraction.py
```

### Integration Tests (Real LLM)

```bash
# Test with real LLM on sample minute
OPENAI_API_KEY=sk-xxx... LEGISLATURE=56 MINUTE_REF=0001 python compute_attendance_job.py
```

### Manual Validation

1. Process a sample minute with known attendance
2. Compare LLM output with original HTML
3. Calculate precision/recall:
   - **Precision**: % of extracted members that are correct
   - **Recall**: % of actual members that were extracted
4. Tune threshold and prompt based on results

## Troubleshooting

### "No LLM provider configured"

**Problem**: No API key found in environment

**Solution**: Set `OPENAI_API_KEY` or `AZURE_OPENAI_ENDPOINT` in `.env` file

### "LLM Connection Error"

**Problem**: Cannot connect to LLM API

**Solutions**:
- Check internet connection
- Verify API key is valid
- Check firewall/proxy settings

### "LLM Rate Limit Error"

**Problem**: Too many API requests

**Solutions**:
- Add delays between requests
- Use smaller batches
- Upgrade API tier
- Switch to Azure OpenAI (higher limits)

### Low match rate (many unmatched names)

**Problem**: Fuzzy matching threshold too high

**Solutions**:
- Lower `FUZZY_MATCH_THRESHOLD` (try 80-85)
- Check for typos in database member names
- Improve prompt to extract full names

### Wrong member matches

**Problem**: Fuzzy matching threshold too low

**Solutions**:
- Increase `FUZZY_MATCH_THRESHOLD` (try 90-95)
- Add manual validation step
- Improve LLM prompt for more accurate names

## Next Steps

### High Priority

1. **Implement attendance repository `create()` method**
   - Store extracted attendance in database
   - Handle duplicates (ON CONFLICT)

2. **Add vote extraction**
   - Similar LLM approach for vote records
   - Extract vote position (for/against/abstention)

3. **Integration testing**
   - Test full pipeline end-to-end
   - Validate accuracy with sample data

### Medium Priority

4. **Batch processing optimization**
   - Process multiple minutes in parallel
   - Rate limiting and retry logic

5. **Caching layer**
   - Store LLM responses in database
   - Avoid reprocessing on retries

6. **Error recovery**
   - Resume failed batches
   - Partial success handling

### Low Priority

7. **Alternative LLM providers**
   - Anthropic Claude implementation
   - Ollama local LLM support

8. **Cost reporting**
   - Track token usage per job
   - Cost estimates and budgets

9. **Performance monitoring**
   - Processing time metrics
   - Accuracy tracking over time

## References

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- [RapidFuzz Documentation](https://rapidfuzz.github.io/RapidFuzz/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
