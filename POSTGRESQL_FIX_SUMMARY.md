# PostgreSQL Connection Issue - COMPLETE RESOLUTION

## Problem Summary
NotebookLlama Streamlit application on Windows could not connect to Docker PostgreSQL container despite correct configuration. Connection attempts failed with "password authentication failed for user raguser".

## Root Cause ✅
**Port Conflict:** Local Windows PostgreSQL 17 service running on port 5432 was intercepting all connection attempts intended for Docker PostgreSQL.

**Evidence:**
```bash
# Two processes listening on port 5432:
PID 6604:  postgres (Windows PostgreSQL 17)
PID 27536: com.docker.backend (Docker port forwarding)
```

When connecting to `127.0.0.1:5432`, Python was connecting to the Windows PostgreSQL instance, not the Docker container. This explains why:
- ❌ Password authentication always failed (wrong PostgreSQL instance)
- ❌ pg_hba.conf changes had no effect (applied to Docker, but connections went to Windows)
- ❌ No connection logs in Docker PostgreSQL (connections never reached it)

## Solution Implemented ✅

### 1. Changed Docker PostgreSQL Port
Modified `docker-compose.local.yml`:
```yaml
ports:
  - "5433:5432"  # Changed from "5432:5432"
```

### 2. Updated Environment Variables
Modified `.env`:
```bash
DATABASE_URL=postgresql://raguser:secure_password@127.0.0.1:5433/notebookllama_rag
PGVECTOR_PORT=5433  # Changed from 5432
```

### 3. Restarted Docker Container
```bash
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d postgresql
```

## Verification ✅

### Connection Test
```bash
python -c "import psycopg2; conn = psycopg2.connect(host='127.0.0.1', port='5433', database='notebookllama_rag', user='raguser', password='secure_password'); print('SUCCESS'); conn.close()"
```

**Result:** ✅ SUCCESS - Connected to Docker PostgreSQL on port 5433

### PostgreSQL Version Check
```bash
python -c "import psycopg2; conn = psycopg2.connect(host='127.0.0.1', port='5433', database='notebookllama_rag', user='raguser', password='secure_password'); cur = conn.cursor(); cur.execute('SELECT version()'); print(cur.fetchone()[0]); conn.close()"
```

**Result:** PostgreSQL 16.10 (Debian 16.10-1.pgdg12+1) on x86_64-pc-linux-gnu

### Connection Logs
Docker PostgreSQL logs now show successful connections:
```
2025-11-08 22:06:31.434 UTC [35] LOG:  connection received: host=172.18.0.1 port=56192
2025-11-08 22:06:31.436 UTC [35] LOG:  connection authorized: user=raguser database=notebookllama_rag
2025-11-08 22:06:31.443 UTC [35] LOG:  disconnection: session time: 0:00:00.009 user=raguser database=notebookllama_rag host=172.18.0.1 port=56192
```

## Key Insights

1. **Port Conflicts on Windows** - Windows services can silently intercept connections even when Docker port forwarding is configured
2. **Connection Source IP** - Connections from Windows host to Docker container appear as 172.18.0.1 (Docker gateway), not 127.0.0.1
3. **pg_hba.conf** - The trust authentication rule for 172.18.0.0/16 works correctly once the right instance is reached
4. **Debugging Approach** - Check `netstat` and process IDs when Docker port forwarding mysteriously fails

## Files Modified

1. `docker-compose.local.yml` - Changed PostgreSQL port mapping to 5433:5432
2. `.env` - Updated PGVECTOR_PORT and DATABASE_URL to use port 5433
3. `pg_hba.conf` (in container) - Added Docker subnet trust rule (this was already correct)

## Current Configuration

### Docker Compose
```yaml
postgresql:
  image: pgvector/pgvector:pg16
  ports:
    - "5433:5432"  # Docker PostgreSQL accessible on port 5433
```

### Environment Variables
```bash
PGVECTOR_HOST=127.0.0.1
PGVECTOR_PORT=5433
PGVECTOR_DATABASE=notebookllama_rag
PGVECTOR_USER=raguser
PGVECTOR_PASSWORD=secure_password
```

### Port Allocation
- **5432** - Windows PostgreSQL 17 (local service)
- **5433** - Docker PostgreSQL 16 (notebookllama container)

## Testing Commands

```bash
# Test Docker PostgreSQL
python -c "import psycopg2; conn = psycopg2.connect(host='127.0.0.1', port='5433', database='notebookllama_rag', user='raguser', password='secure_password'); print('Docker PostgreSQL: OK'); conn.close()"

# Check container status
docker ps --filter "name=postgresql"

# View connection logs
docker logs notebookllama-postgresql-1 --tail 10

# Check port listeners
netstat -ano | findstr :5433
```

## Status

✅ **RESOLVED** - PostgreSQL connection working correctly on port 5433

## Related Documentation

- `POSTGRESQL_DEBUG_PROMPT.md` - Original problem description
- `POSTGRESQL_SOLUTION.md` - Detailed solution options
- `pg_hba.conf` - PostgreSQL authentication configuration (in container)

## Lessons Learned

1. Always check for port conflicts when Docker port forwarding doesn't work
2. Use `netstat -ano` and process ID lookup to identify conflicting services
3. Docker Desktop on Windows adds complexity to localhost networking
4. PostgreSQL authentication issues can be symptoms of connectivity problems
5. Enable connection logging (`log_connections=on`) early in debugging

---

**Problem Duration:** Several hours of troubleshooting
**Time to Fix:** 5 minutes once root cause was identified
**Key Tool:** `netstat -ano` to identify port conflicts
