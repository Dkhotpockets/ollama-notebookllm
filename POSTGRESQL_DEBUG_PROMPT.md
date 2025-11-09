# PostgreSQL Authentication Issue - Debug Prompt for Claude

## Problem Summary
A NotebookLlama Streamlit application on Windows cannot connect to a local PostgreSQL Docker container from the host machine, despite correct configuration. Internal container connections work, but external psycopg2 connections consistently fail with "password authentication failed for user raguser".

## Environment Details
- **OS**: Windows 11
- **Docker**: Docker Desktop with WSL2 backend
- **PostgreSQL**: pgvector/pgvector:pg16 (PostgreSQL 16.10)
- **Python**: 3.13
- **Connection Library**: psycopg2

## Current Configuration

### Docker Compose (docker-compose.local.yml)
```yaml
services:
  postgresql:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: notebookllama_rag
      POSTGRES_USER: raguser
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ragflow_network
```

### Environment Variables (.env)
```
PGVECTOR_HOST=127.0.0.1
PGVECTOR_PORT=5432
PGVECTOR_USER=raguser
PGVECTOR_PASSWORD=secure_password
PGVECTOR_DATABASE=notebookllama_rag
```

## Symptoms

1. **Internal connections work**: `docker exec notebookllama-postgresql-1 psql -U raguser -d notebookllama_rag` succeeds
2. **External connections fail**: `psycopg2.connect(host='127.0.0.1', port=5432, ...)` fails with:
   ```
   psycopg2.OperationalError: connection to server at "127.0.0.1", port 5432 failed: 
   FATAL: password authentication failed for user "raguser"
   ```
3. **Port is accessible**: `Test-NetConnection -Port 5432` succeeds
4. **No PostgreSQL logs**: Connection attempts don't appear in PostgreSQL logs even with `log_connections=on`

## Troubleshooting Already Attempted

### 1. Password Resets
- Multiple `ALTER USER raguser WITH PASSWORD 'secure_password'` attempts
- Both encrypted and unencrypted password variations
- Fresh container initialization with volumes removed

### 2. Authentication Method Changes
- Modified pg_hba.conf from md5 to scram-sha-256 (matching `SHOW password_encryption`)
- Tried trust authentication
- Current pg_hba.conf:
```
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
host    all             all             0.0.0.0/0               scram-sha-256
```

### 3. Network Configuration
- Changed PGVECTOR_HOST from "localhost" to "127.0.0.1" (avoid IPv6)
- Verified listen_addresses = '*' in postgresql.conf
- Attempted connection via Docker internal IP (172.18.0.2) - timeout
- Container restart and full recreation with fresh volumes

### 4. User Verification
- Confirmed raguser exists: `SELECT rolname FROM pg_roles WHERE rolname='raguser'` returns raguser
- Verified login capability: `rolcanlogin = t`
- Password hash stored correctly in pg_authid

## Key Observations

1. **Trust authentication for 127.0.0.1/32 doesn't work from host** - should allow passwordless connection but still requires password
2. **No authentication logs generated** - suggests connection may not be reaching PostgreSQL's authentication layer
3. **Container internal auth works immediately** - no PGPASSWORD needed for docker exec psql
4. **Consistent failure across multiple recreations** - not a stale configuration issue

## Question for Claude

**How can I fix PostgreSQL authentication to allow external connections from the Windows host to the Docker PostgreSQL container?**

Specifically:
- Why doesn't the `trust` authentication for 127.0.0.1/32 work from the host?
- Why are no connection attempts logged even with log_connections enabled?
- Is there a Windows Docker Desktop networking quirk affecting PostgreSQL authentication?
- Should I modify the Docker network configuration or use host networking mode?

## Expected Outcome
The following Python code should successfully connect:
```python
import psycopg2
conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    database='notebookllama_rag',
    user='raguser',
    password='secure_password'
)
print('✓ Connected successfully')
conn.close()
```

## Additional Context
- The Streamlit application works perfectly with Supabase as an alternative
- PostgreSQL is only needed for optional observability/tracing features
- Application has graceful error handling for PostgreSQL unavailability
- Current workaround: Use Supabase for all database operations

## Files to Reference
- Docker Compose: `docker-compose.local.yml`
- Environment: `.env`
- Observability Dashboard: `src/notebookllama/pages/4_Observability_Dashboard.py`
- Container: `notebookllama-postgresql-1`

## Commands to Test Solution
```bash
# Test connection
python -c "import psycopg2; conn = psycopg2.connect(host='127.0.0.1', port='5432', database='notebookllama_rag', user='raguser', password='secure_password'); print('✓ Connected'); conn.close()"

# Verify user inside container
docker exec notebookllama-postgresql-1 psql -U raguser -d notebookllama_rag -c "SELECT current_user;"

# Check PostgreSQL logs
docker logs notebookllama-postgresql-1 --tail 50

# View pg_hba.conf
docker exec notebookllama-postgresql-1 cat /var/lib/postgresql/data/pg_hba.conf
```
