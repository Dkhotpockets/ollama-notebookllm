# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- fix: Close DB connections and dispose SQLAlchemy engines on disconnect to avoid SQLite file locks on Windows. This prevents PermissionError/WinError when running tests and cleanup.
- fix: Add retry logic for crawl job upserts to improve resilience against transient storage failures.
- feat: Add UI retry controls and per-resource retry buttons in Topic Discovery page so users can re-run failed crawls without re-running the entire pipeline.
- test: Add tests validating DB disconnect behavior and updated DB tests to prefer DATABASE_URL when available.

### Verification

- Local test suite: 91 passed, 2 skipped, 3 warnings (local run on Windows).
- Manual/end-to-end crawl test (`tests/test_storage.py`) verified crawl+storage pipeline with retry logic.

### Notes

- If you rely on the local `pgvector` Postgres container, there are environment-specific caveats (password encryption scram-sha-256 vs md5 and Docker Desktop volumes/init ordering). Supabase fallback is available and recommended for quick operation.
