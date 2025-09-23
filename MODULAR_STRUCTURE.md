# Modular Code Structure

## Overview

The codebase has been refactored into a modular architecture with clear separation of concerns. This document explains the new structure and how to use it.

## Directory Structure

```
├── src/
│   ├── core/                    # Core RAG functionality
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication & token management
│   │   ├── embeddings.py       # Embedding operations & similarity
│   │   ├── chunking.py         # Document processing & adaptive chunking
│   │   ├── search.py           # Query classification & adaptive search
│   │   ├── llm.py              # GPT-5 interaction
│   │   └── config.py           # Configuration constants
│   │
│   ├── enhanced/                # Enhanced RAG with decomposition
│   │   ├── __init__.py
│   │   ├── decomposition.py    # Query decomposition logic
│   │   ├── execution.py        # Sub-query execution
│   │   ├── synthesis.py        # Result synthesis
│   │   └── orchestrator.py     # Enhanced RAG orchestrator
│   │
│   ├── general_purpose_rag.py          # Original monolithic file (legacy)
│   ├── general_purpose_rag_new.py      # New modular implementation
│   └── enhanced_rag.py                 # Original enhanced RAG (legacy)
│
├── server/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py              # API route definitions
│   │   └── static.py           # Static file serving
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── query_handler.py    # Query processing logic
│   │   └── document_handler.py # Document loading
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── response.py         # Response formatting utilities
│   │
│   └── app.py                  # Flask app initialization
│
├── static/
│   ├── js/
│   │   ├── core/
│   │   │   ├── api-client.js   # API communication
│   │   │   └── state-manager.js # Application state
│   │   │
│   │   ├── utils/
│   │   │   └── formatters.js   # Utility functions
│   │   │
│   │   └── main.js             # Main app initialization
│   │
│   └── css/
│       ├── components.css      # Component styles
│       └── globals.css         # Global styles
│
├── server.py                   # Original monolithic server (legacy)
├── server_new.py               # New modular server entry point
└── app.js                      # Original monolithic frontend (legacy)
```

## Key Modules

### Backend Core (`src/core/`)

- **auth.py**: Handles authentication and token management
  - `AuthManager` class for token lifecycle

- **embeddings.py**: Embedding operations
  - `EmbeddingService` for generating embeddings
  - Cosine similarity calculations

- **chunking.py**: Document processing
  - `ChunkingService` for adaptive chunking
  - Content type detection
  - Caching mechanism

- **search.py**: Search functionality
  - `SearchService` for query classification
  - Adaptive search based on query type

- **llm.py**: LLM interaction
  - `LLMService` for GPT-5 queries
  - Chain of Thought reasoning

- **config.py**: Centralized configuration
  - Environment variable loading
  - Pattern definitions
  - Chunk size configuration

### Enhanced RAG (`src/enhanced/`)

- **decomposition.py**: Query decomposition
  - `QueryDecomposer` for breaking complex queries
  - Complexity assessment

- **execution.py**: Sub-query execution
  - `SubQueryExecutor` for parallel execution
  - Progress tracking

- **synthesis.py**: Result synthesis
  - `ResultSynthesizer` for combining results

- **orchestrator.py**: Main enhanced RAG
  - `EnhancedRAG` class coordinating all components

### Server (`server/`)

- **routes/api.py**: API endpoints
- **routes/static.py**: Static file serving
- **handlers/query_handler.py**: Query processing
- **handlers/document_handler.py**: Document management
- **utils/response.py**: Response utilities

### Frontend (`static/js/`)

- **core/api-client.js**: API communication
- **core/state-manager.js**: State management
- **utils/formatters.js**: Formatting utilities
- **main.js**: Application entry point

## Usage

### Running the Modular Server

```bash
python server_new.py
```

### Using the Modular Backend

```python
from src.enhanced.orchestrator import EnhancedRAG

# Initialize
rag = EnhancedRAG()

# Load document
rag.load_and_process_document("test.txt")

# Query
result = rag.enhanced_query("Your question here")
```

### Legacy vs New

- **Legacy files** (kept for compatibility):
  - `src/general_purpose_rag.py`
  - `src/enhanced_rag.py`
  - `server.py`
  - `app.js`

- **New modular files**:
  - `src/general_purpose_rag_new.py`
  - `src/core/*` and `src/enhanced/*`
  - `server/*`
  - `static/js/*`
  - `server_new.py`

## Benefits

1. **Maintainability**: Each module has a single responsibility
2. **Testability**: Isolated components easier to unit test
3. **Scalability**: Add features without touching core logic
4. **Debugging**: Smaller files easier to navigate
5. **Reusability**: Shared utilities across modules
6. **Team Collaboration**: Multiple developers can work simultaneously

## Migration Notes

The original files are preserved for backward compatibility. Once the new structure is tested and verified, the legacy files can be deprecated.

## Testing

Test the modular structure:

```bash
# Test new general purpose RAG
cd src
python general_purpose_rag_new.py

# Test enhanced RAG
cd src/enhanced
python orchestrator.py

# Test server
python server_new.py
```