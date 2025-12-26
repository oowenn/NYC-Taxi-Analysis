# NYC Uber/Lyft Data Chatbot

LLM-powered chatbot for querying NYC TLC FHVHV (For-Hire Vehicle High Volume) data using natural language. Generates SQL queries, executes them with DuckDB, and creates visualizations.

## Features

- 🤖 Natural language to SQL generation using LLMs (Ollama)
- 📊 Structured chart specification generation (JSON specs instead of Python code)
- 🎯 Agent-style validation with automatic error correction and retry logic
- ⚡ Fast queries using DuckDB on Parquet files
- 📈 Reliable chart rendering from structured specifications
- 🌐 Web interface for interactive querying

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Ollama installed and running
- Data files in `data/` directory

### Setup

1. **Install dependencies:**
   ```bash
   make setup
   # Or manually:
   # Backend: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   # Frontend: cd frontend && npm install
   ```

2. **Start Ollama and pull model:**
   ```bash
   ollama serve  # In a separate terminal
   ollama pull llama3:latest
   ```

3. **Prepare data:**
   
   **Download trip data from NYC TLC:**
   - Download `fhvhv_tripdata_2023-*.parquet` files from the [NYC TLC Trip Record Data page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
   - Look for "High Volume For-Hire Vehicle Trip Records" under the 2023 section
   - Place the downloaded Parquet files in the `data/` directory
   
   **Lookup files:**
   - `taxi_zone_lookup.csv` - Available from the NYC TLC website (Taxi Zone Lookup Table), but also included in `data/`
   - `fhv_base_lookup.csv` - Created for this project, included in `data/`
   - `hvfhs_license_num_lookup.csv` - Created for this project, included in `data/`
   
   All lookup files should be placed in the `data/` directory.

4. **Configure environment:**
   ```bash
   cp .env.example backend/.env
   # Edit backend/.env if needed (defaults should work for local dev)
   ```

### Running the Server

**Start backend (Terminal 1):**
```bash
make backend-dev
# Or manually:
# cd backend && source venv/bin/activate && USE_LLM_PIPELINE=true uvicorn main:app --reload --port 8000
```

**Start frontend (Terminal 2):**
```bash
make frontend-dev
# Or manually:
# cd frontend && npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Usage

1. Open http://localhost:5173 in your browser
2. Ask questions about the NYC Uber/Lyft data, for example:
   - "What are the top 10 pickup zones?"
   - "Show hourly trips by company for the first 3 days of January 2023"
   - "What is the percentage of base passenger fares held by each company?"
3. View the generated SQL, data table, and visualization

## Testing the LLM Pipeline

The main test script (`backend/scripts/test_llm_pipeline.py`) implements the full pipeline:

**Pipeline Flow:**
1. User question → LLM generates SQL (with validation/retry)
2. SQL → DuckDB executes query
3. Query results → LLM generates chart spec (with validation/retry)
4. Chart spec → Renderer generates visualization

### Prerequisites

- Python 3.10+
- Ollama installed and running
- Data files in `data/` directory

### Setup

1. **Install dependencies:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start Ollama and pull model:**
```bash
ollama serve  # In a separate terminal
ollama pull llama3
```

3. **Prepare data:**
   
   **Download trip data from NYC TLC:**
   - Download `fhvhv_tripdata_2023-*.parquet` files from the [NYC TLC Trip Record Data page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
   - Look for "High Volume For-Hire Vehicle Trip Records" under the 2023 section
   - Place the downloaded Parquet files in the `data/` directory
   
   **Lookup files:**
   - `taxi_zone_lookup.csv` - Available from the NYC TLC website (Taxi Zone Lookup Table), but also included in `data/`
   - `fhv_base_lookup.csv` - Created for this project, included in `data/`
   - `hvfhs_license_num_lookup.csv` - Created for this project, included in `data/`
   
   All lookup files should be placed in the `data/` directory.

### Running Tests

**Test the full LLM pipeline:**
```bash
cd backend
source venv/bin/activate
PYTHONPATH=. OLLAMA_MODEL=llama3 python scripts/test_llm_pipeline.py
```

**Test SQL generation only:**
```bash
PYTHONPATH=. OLLAMA_MODEL=llama3 python scripts/test_sql_generation.py
```

**Using Makefile:**
```bash
make test-llm-pipeline
```

### Environment Variables

- `OLLAMA_MODEL`: Model to use (default: `llama3`)
- `OLLAMA_BASE_URL`: Ollama server URL (default: `http://127.0.0.1:11434`)
- `LLM_TIMEOUT`: Timeout in seconds (default: `180`)
- `MAX_SQL_ATTEMPTS`: Max retries for SQL generation (default: `3`)
- `MAX_SPEC_ATTEMPTS`: Max retries for chart spec generation (default: `3`)

### Output

The test script will:
1. Generate and validate SQL
2. Execute the query and show sample results
3. Generate a structured chart specification
4. Render the chart using matplotlib
5. Save the chart to `backend/scripts/llm_chart.png`

### Validation Features

- **SQL Validation**: Checks syntax, schema (column existence), safety (dangerous keywords), and execution
- **Chart Spec Validation**: Validates JSON structure, column existence, and data types
- **Retry Logic**: Automatically retries with error feedback (up to 3 attempts each)
- **Error Feedback**: Feeds validation errors back to LLM for self-correction

## Project Structure

```
.
├── backend/
│   ├── scripts/
│   │   ├── test_llm_pipeline.py    # Main pipeline test
│   │   ├── test_sql_generation.py  # SQL generation test
│   │   ├── validation.py           # Validation tools
│   │   └── chart_renderer.py       # Chart renderer from specs
│   ├── db/
│   │   └── duckdb_setup.py         # DuckDB initialization
│   └── requirements.txt
├── data/                           # Parquet files (gitignored)
└── Makefile                        # Development commands
```

## License

MIT
