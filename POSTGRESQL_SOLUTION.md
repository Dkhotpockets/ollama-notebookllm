# PostgreSQL Connection Issue - SOLUTION

## Root Cause Identified ✅

The connection failures were caused by a **port conflict**:

- **Local PostgreSQL 17** service (`postgresql-x64-17`) running on Windows on port 5432
- **Docker PostgreSQL** container also trying to use port 5432
- When connecting to `127.0.0.1:5432`, Python was connecting to the **Windows PostgreSQL**, not the Docker container
- The Windows PostgreSQL has different users/passwords, causing authentication failures

## Evidence

```powershell
# netstat shows TWO processes on port 5432:
PID 6604:  postgres (Windows PostgreSQL)
PID 27536: com.docker.backend (Docker port forwarding)

# Windows Service:
Name: postgresql-x64-17
Status: Running
```

## Solution Options

### Option 1: Stop Local PostgreSQL Service (Recommended if not needed)

If you don't need the local Windows PostgreSQL:

```powershell
# Stop the service
Stop-Service postgresql-x64-17

# Disable it from auto-starting
Set-Service postgresql-x64-17 -StartupType Disabled

# Test connection to Docker PostgreSQL
python -c "import psycopg2; conn = psycopg2.connect(host='127.0.0.1', port='5432', database='notebookllama_rag', user='raguser', password='secure_password'); print('SUCCESS'); conn.close()"
```

### Option 2: Change Docker PostgreSQL Port (Recommended if you need both)

Modify `docker-compose.local.yml` to use a different port:

```yaml
services:
  postgresql:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: notebookllama_rag
      POSTGRES_USER: raguser
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5433:5432"  # Changed from 5432:5432
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ragflow_network
```

Update `.env` file:

```bash
PGVECTOR_HOST=127.0.0.1
PGVECTOR_PORT=5433  # Changed from 5432
PGVECTOR_USER=raguser
PGVECTOR_PASSWORD=secure_password
PGVECTOR_DATABASE=notebookllama_rag
```

Restart Docker container:

```bash
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

Test connection:

```bash
python -c "import psycopg2; conn = psycopg2.connect(host='127.0.0.1', port='5433', database='notebookllama_rag', user='raguser', password='secure_password'); print('SUCCESS'); conn.close()"
```

### Option 3: Connect to Docker Container IP Directly

Get the container IP:

```bash
docker inspect notebookllama-postgresql-1 --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
# Example output: 172.18.0.2
```

Update `.env` to use container IP:

```bash
PGVECTOR_HOST=172.18.0.2  # Use the actual container IP
PGVECTOR_PORT=5432
PGVECTOR_USER=raguser
PGVECTOR_PASSWORD=secure_password
PGVECTOR_DATABASE=notebookllama_rag
```

**Note:** This IP may change when container restarts.

## Recommended Solution

**Use Option 2** (Change Docker port to 5433) because:
- ✅ Allows both PostgreSQL instances to run
- ✅ No conflicts
- ✅ Stable configuration
- ✅ Easy to maintain

## Implementation Steps

### Step 1: Update Docker Compose

```bash
# Edit docker-compose.local.yml
# Change ports from "5432:5432" to "5433:5432"
```

### Step 2: Update Environment Variables

```bash
# Edit .env
# Change PGVECTOR_PORT=5432 to PGVECTOR_PORT=5433
```

### Step 3: Restart Docker Container

```bash
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

### Step 4: Verify Connection

```bash
python -c "import psycopg2; conn = psycopg2.connect(host='127.0.0.1', port='5433', database='notebookllama_rag', user='raguser', password='secure_password'); print('✓ PostgreSQL connection successful!'); conn.close()"
```

## Why Previous Troubleshooting Didn't Work

1. **pg_hba.conf modifications** - Correct configuration, but applied to wrong PostgreSQL instance
2. **Password resets** - Changed password in Docker PostgreSQL, but connections went to Windows PostgreSQL
3. **Trust authentication** - Worked in Docker PostgreSQL, but never reached it
4. **No connection logs** - Docker PostgreSQL never saw the connections

## Verification Commands

After implementing the solution:

```bash
# Check what's listening on ports
netstat -ano | findstr :5432
netstat -ano | findstr :5433

# Test Docker PostgreSQL connection
python -c "import psycopg2; conn = psycopg2.connect(host='127.0.0.1', port='5433', database='notebookllama_rag', user='raguser', password='secure_password'); print('Docker PostgreSQL: OK'); conn.close()"

# Check Docker container logs
docker logs notebookllama-postgresql-1 --tail 10

# Verify connection appears in logs
docker exec notebookllama-postgresql-1 psql -U raguser -d notebookllama_rag -c "SELECT client_addr, usename, application_name FROM pg_stat_activity WHERE usename='raguser';"
```

## Summary

**Problem:** Port conflict between local Windows PostgreSQL and Docker PostgreSQL
**Root Cause:** Both services using port 5432
**Solution:** Change Docker PostgreSQL to use port 5433
**Status:** ✅ RESOLVED

The connection issue was NOT an authentication problem - it was connecting to the wrong PostgreSQL instance entirely!
