Fixes for DB disconnect handling, crawl job upsert retries, Topic Discovery retry UI, and tests.

Verification: Local test suite: 91 passed, 2 skipped, 3 warnings. End-to-end crawl tests passed.

Notes: If you rely on a local pgvector Postgres container, watch for scram-sha-256 vs md5 and Docker Desktop volume init issues. Supabase fallback recommended for quick operation.
