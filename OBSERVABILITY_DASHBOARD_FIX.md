# Observability Dashboard - PostgreSQL Connection Fix

## Issue
The Observability Dashboard was showing "PostgreSQL connection failed" errors because it was trying to connect to port 5432 instead of the updated port 5433.

## Root Cause
The Streamlit application needed to be restarted to pick up the updated `.env` file with the new PostgreSQL port configuration.

## Solution Applied ✅

### 1. Fixed Hardcoded Port in test_db_connection.py
**File:** `test_db_connection.py:18`

**Before:**
```python
engine_url = f"postgresql+psycopg2://{os.getenv('PGVECTOR_USER')}:{os.getenv('PGVECTOR_PASSWORD')}@localhost:5432/{os.getenv('PGVECTOR_DATABASE')}"
```

**After:**
```python
port = os.getenv('PGVECTOR_PORT', '5433')
engine_url = f"postgresql+psycopg2://{os.getenv('PGVECTOR_USER')}:{os.getenv('PGVECTOR_PASSWORD')}@localhost:{port}/{os.getenv('PGVECTOR_DATABASE')}"
```

### 2. Restarted Streamlit Application
The new Streamlit instance is running on **port 8503** with the updated environment variables.

**Access it at:** http://localhost:8503

## Verification

### Connection Test
```bash
python test_db_connection.py
```

**Expected Output:**
```
Engine URL: postgresql+psycopg2://raguser:***@localhost:5433/notebookllama_rag
[SUCCESS] DocumentManager created successfully
[SUCCESS] Database connection successful, found 0 documents
```

### Observability Dashboard Access
1. Navigate to http://localhost:8503
2. Go to "Observability Dashboard" page
3. Dashboard should now show "No trace data available yet" instead of connection errors

## Current Configuration

### Environment Variables (.env)
```bash
PGVECTOR_HOST=127.0.0.1
PGVECTOR_PORT=5433
PGVECTOR_DATABASE=notebookllama_rag
PGVECTOR_USER=raguser
PGVECTOR_PASSWORD=secure_password
```

### Docker PostgreSQL
```
Container: notebookllama-postgresql-1
Port Mapping: 5433:5432
Status: Running
```

### Streamlit Application
```
Old instance (outdated env): http://localhost:8502
New instance (updated env): http://localhost:8503  ← USE THIS ONE
```

## How the Observability Dashboard Works

The dashboard reads PostgreSQL configuration from environment variables:

```python
# From src/notebookllama/pages/4_Observability_Dashboard.py
pgvector_user = os.getenv('PGVECTOR_USER')
pgvector_password = os.getenv('PGVECTOR_PASSWORD')
pgvector_host = os.getenv('PGVECTOR_HOST', 'localhost')
pgvector_port = os.getenv('PGVECTOR_PORT', '5432')  # Defaults to 5432
pgvector_database = os.getenv('PGVECTOR_DATABASE')

engine_url = f"postgresql+psycopg2://{pgvector_user}:{pgvector_password}@{pgvector_host}:{pgvector_port}/{pgvector_database}"
```

Since we set `PGVECTOR_PORT=5433` in `.env`, it now connects to the correct port.

## Trace Data Collection

The Observability Dashboard displays trace data from the `agent_traces` table. To populate it:

1. **Enable tracing in Home.py** (currently disabled):
   - Uncomment the instrumentation code (lines 31-44)
   - Uncomment the SQL engine initialization
   - Uncomment the trace recording (line 84)

2. **Process a document:**
   - Upload a PDF on the Home page
   - Click "Process Document"
   - Traces will be automatically recorded

3. **View traces:**
   - Navigate to Observability Dashboard
   - Charts will show latency, operation count, and trace timeline

## Troubleshooting

### If Dashboard Still Shows Connection Error

**Check environment variables are loaded:**
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'PGVECTOR_PORT: {os.getenv(\"PGVECTOR_PORT\")}')"
```

**Expected:** `PGVECTOR_PORT: 5433`

**Restart Streamlit:**
```bash
# Stop old instances
tasklist | findstr streamlit
# Then kill the processes or restart your terminal

# Start new instance
streamlit run src/notebookllama/Home.py --server.port=8503
```

### If PostgreSQL Connection Fails

**Verify PostgreSQL is running:**
```bash
docker ps --filter "name=postgresql"
```

**Test direct connection:**
```bash
python -c "import psycopg2; conn = psycopg2.connect(host='127.0.0.1', port='5433', database='notebookllama_rag', user='raguser', password='secure_password'); print('OK'); conn.close()"
```

## Summary

✅ **Fixed:** Hardcoded port 5432 in test_db_connection.py
✅ **Updated:** Now uses PGVECTOR_PORT environment variable
✅ **Tested:** Connection successful to PostgreSQL on port 5433
✅ **Status:** Observability Dashboard ready to use

**New Streamlit URL:** http://localhost:8503
**PostgreSQL Port:** 5433
**Connection:** Working ✅
