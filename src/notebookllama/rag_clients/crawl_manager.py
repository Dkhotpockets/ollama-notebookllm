"""
Crawl4AI Web Crawling Manager for NotebookLlama
Enhanced from RAGFlow-Slim integration
"""

import os
import logging
import asyncio
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    AsyncWebCrawler = None


class CrawlStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CrawlJobRequest:
    """Request model for crawl job"""
    url: str
    extract_entities: bool = True
    politeness_delay: float = 1.0
    max_pages: int = 1
    follow_links: bool = False
    respect_robots_txt: bool = True
    timeout: float = 30.0
    user_agent: str = "NotebookLlama-Crawler/1.0"
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class CrawlJobResponse:
    """Response model for crawl job"""
    job_id: str
    url: str
    status: CrawlStatus
    content: Optional[str] = None
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None


class CrawlJobManager:
    """Manager for web crawling jobs with storage backend"""
    
    def __init__(self, storage_client=None):
        self.storage_client = storage_client
        self._local_jobs: Dict[str, CrawlJobResponse] = {}
        self._rate_limiter = RateLimiter()
    
    def _generate_job_id(self, url: str) -> str:
        """Generate unique job ID from URL"""
        timestamp = datetime.now().isoformat()
        content = f"{url}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def create_job(self, request: CrawlJobRequest) -> CrawlJobResponse:
        """Create a new crawl job"""
        job_id = self._generate_job_id(request.url)
        
        job = CrawlJobResponse(
            job_id=job_id,
            url=request.url,
            status=CrawlStatus.PENDING,
            metadata=request.metadata or {},
            created_at=datetime.now()
        )
        
        # Store job
        await self._store_job(job)
        
        logger.info(f"Created crawl job {job_id} for URL: {request.url}")
        return job
    
    async def execute_job(self, job_id: str, request: CrawlJobRequest) -> CrawlJobResponse:
        """Execute a crawl job"""
        if not CRAWL4AI_AVAILABLE:
            error = "Crawl4AI not available - install with: pip install crawl4ai"
            return await self._update_job_status(job_id, CrawlStatus.FAILED, error=error)
        
        # Check rate limiting
        if not await self._rate_limiter.can_crawl(request.url):
            error = f"Rate limited for domain: {request.url}"
            return await self._update_job_status(job_id, CrawlStatus.FAILED, error=error)
        
        # Update status to running
        job = await self._update_job_status(job_id, CrawlStatus.RUNNING)
        
        start_time = datetime.now()
        
        try:
            # Configure crawler
            crawler_config = {
                "headless": True,
                "verbose": False,
                "timeout": request.timeout,
                "user_agent": request.user_agent
            }
            
            async with AsyncWebCrawler(**crawler_config) as crawler:
                # Check robots.txt if required
                if request.respect_robots_txt:
                    if not await self._check_robots_txt(request.url):
                        error = "Crawling disallowed by robots.txt"
                        return await self._update_job_status(job_id, CrawlStatus.FAILED, error=error)
                
                # Apply politeness delay
                if request.politeness_delay > 0:
                    await asyncio.sleep(request.politeness_delay)
                
                # Perform crawl
                result = await crawler.arun(url=request.url)
                
                if result.success:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    # Extract content and metadata
                    content = result.markdown or result.html
                    title = getattr(result, 'title', '') or self._extract_title_from_content(content)
                    
                    metadata = {
                        **(request.metadata or {}),
                        "title": title,
                        "url": request.url,
                        "crawled_at": datetime.now().isoformat(),
                        "content_length": len(content) if content else 0,
                        "processing_time": processing_time
                    }
                    
                    # Update job with results
                    job = await self._update_job_status(
                        job_id, 
                        CrawlStatus.COMPLETED,
                        content=content,
                        title=title,
                        metadata=metadata,
                        processing_time=processing_time
                    )
                    
                    logger.info(f"Crawl job {job_id} completed successfully")
                    return job
                    
                else:
                    error = f"Crawl failed: {getattr(result, 'error', 'Unknown error')}"
                    return await self._update_job_status(job_id, CrawlStatus.FAILED, error=error)
                    
        except asyncio.TimeoutError:
            error = f"Crawl timeout after {request.timeout}s"
            return await self._update_job_status(job_id, CrawlStatus.FAILED, error=error)
            
        except Exception as e:
            error = f"Crawl error: {str(e)}"
            return await self._update_job_status(job_id, CrawlStatus.FAILED, error=error)
    
    async def create_and_execute_job(self, request: CrawlJobRequest) -> CrawlJobResponse:
        """Create and immediately execute a crawl job"""
        job = await self.create_job(request)
        return await self.execute_job(job.job_id, request)
    
    async def get_job(self, job_id: str) -> Optional[CrawlJobResponse]:
        """Get job status and results"""
        # Try storage client first
        if self.storage_client:
            try:
                # Query by job_id column, not id (which is UUID primary key)
                result = self.storage_client.table("crawl_jobs").select("*").eq("job_id", job_id).execute()
                if result.data:
                    data = result.data[0]
                    result_json = data.get("result") or {}
                    return CrawlJobResponse(
                        job_id=data["job_id"],
                        url=data["url"],
                        status=CrawlStatus(data["status"]),
                        content=result_json.get("content"),
                        title=result_json.get("title"),
                        metadata=result_json.get("metadata", {}),
                        error=data.get("error"),
                        created_at=data.get("created_at"),
                        completed_at=data.get("completed_at"),
                        processing_time=result_json.get("processing_time")
                    )
            except Exception as e:
                logger.error(f"Error getting job from storage: {e}")
        
        # Fallback to local storage
        return self._local_jobs.get(job_id)
    
    async def list_jobs(self, limit: int = 50, status: Optional[CrawlStatus] = None) -> List[CrawlJobResponse]:
        """List crawl jobs with optional status filter"""
        jobs = []
        
        # Try storage client first
        if self.storage_client:
            try:
                query = self.storage_client.table("crawl_jobs").select("*").order("created_at", desc=True).limit(limit)
                if status:
                    query = query.eq("status", status.value)
                
                result = query.execute()
                
                for data in result.data:
                    job = CrawlJobResponse(
                        job_id=data["id"],
                        url=data["url"],
                        status=CrawlStatus(data["status"]),
                        content=data.get("content"),
                        title=data.get("metadata", {}).get("title"),
                        metadata=data.get("metadata", {}),
                        error=data.get("metadata", {}).get("error"),
                        created_at=data["created_at"],
                        completed_at=data.get("completed_at"),
                        processing_time=data.get("metadata", {}).get("processing_time")
                    )
                    jobs.append(job)
                
                return jobs
                
            except Exception as e:
                logger.error(f"Error listing jobs from storage: {e}")
        
        # Fallback to local storage
        local_jobs = list(self._local_jobs.values())
        if status:
            local_jobs = [job for job in local_jobs if job.status == status]
        
        return sorted(local_jobs, key=lambda x: x.created_at or datetime.min, reverse=True)[:limit]
    
    async def _store_job(self, job: CrawlJobResponse) -> bool:
        """Store job in backend"""
        # Store locally
        self._local_jobs[job.job_id] = job
        
        # Store in database if available
        if self.storage_client:
            try:
                # Map to database schema: crawl_jobs table has columns:
                # id (UUID), job_id (TEXT), url, status, result (JSONB), error, created_at, updated_at, completed_at
                
                # Handle datetime conversion
                def to_iso(dt):
                    if dt is None:
                        return None
                    if isinstance(dt, str):
                        return dt
                    return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
                
                job_data = {
                    "job_id": job.job_id,
                    "url": job.url,
                    "status": job.status.value,
                    "result": {
                        "content": job.content,
                        "title": job.title,
                        "metadata": job.metadata or {},
                        "processing_time": job.processing_time
                    } if job.content else None,
                    "error": job.error,
                    "created_at": to_iso(job.created_at),
                    "completed_at": to_iso(job.completed_at)
                }
                
                # Some storage backends (or transient network issues) may fail briefly.
                # Retry a few times before giving up to reduce flaky failures.
                attempts = 1
                max_attempts = 3
                while attempts <= max_attempts:
                    try:
                        result = self.storage_client.table("crawl_jobs").upsert(job_data).execute()
                        return len(result.data) > 0
                    except Exception as e:
                        logger.warning(f"Upsert attempt {attempts} failed: {e}")
                        if attempts == max_attempts:
                            logger.error(f"Failed to store job after {max_attempts} attempts: {e}")
                            return False
                        await asyncio.sleep(0.5 * attempts)
                        attempts += 1
            except Exception as e:
                logger.error(f"Error storing job (unexpected): {e}")
                return False
        
        return True
    
    async def _update_job_status(self, 
                               job_id: str, 
                               status: CrawlStatus, 
                               content: Optional[str] = None,
                               title: Optional[str] = None,
                               metadata: Optional[Dict] = None,
                               error: Optional[str] = None,
                               processing_time: Optional[float] = None) -> CrawlJobResponse:
        """Update job status and details"""
        
        # Get existing job
        job = await self.get_job(job_id)
        if not job:
            # Create minimal job if not found
            job = CrawlJobResponse(
                job_id=job_id,
                url="unknown",
                status=CrawlStatus.PENDING,
                created_at=datetime.now()
            )
        
        # Update fields
        job.status = status
        if content is not None:
            job.content = content
        if title is not None:
            job.title = title
        if metadata is not None:
            job.metadata = {**(job.metadata or {}), **metadata}
        if error is not None:
            job.error = error
            job.metadata = {**(job.metadata or {}), "error": error}
        if processing_time is not None:
            job.processing_time = processing_time
        
        if status in [CrawlStatus.COMPLETED, CrawlStatus.FAILED, CrawlStatus.CANCELLED]:
            job.completed_at = datetime.now()
        
        # Store updated job
        await self._store_job(job)
        
        return job
    
    async def _check_robots_txt(self, url: str) -> bool:
        """Check if crawling is allowed by robots.txt"""
        try:
            import urllib.robotparser
            from urllib.parse import urljoin, urlparse
            
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            robot_parser = urllib.robotparser.RobotFileParser()
            robot_parser.set_url(robots_url)
            robot_parser.read()
            
            user_agent = "NotebookLlama-Crawler"
            return robot_parser.can_fetch(user_agent, url)
            
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True  # Allow crawling if robots.txt check fails
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract title from content if available"""
        if not content:
            return ""
        
        try:
            # Look for markdown title
            lines = content.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                if line.startswith('# '):
                    return line[2:].strip()
            
            # Fallback to first non-empty line
            for line in lines[:5]:
                line = line.strip()
                if line and not line.startswith('#') and len(line) < 100:
                    return line
                    
        except Exception as e:
            logger.warning(f"Error extracting title: {e}")
        
        return "Untitled"


class RateLimiter:
    """Simple rate limiter for crawling"""
    
    def __init__(self):
        self._last_crawl: Dict[str, datetime] = {}
        self._min_delay = 1.0  # Minimum delay between requests to same domain
    
    async def can_crawl(self, url: str) -> bool:
        """Check if we can crawl this URL based on rate limiting"""
        try:
            from urllib.parse import urlparse
            
            domain = urlparse(url).netloc
            now = datetime.now()
            
            if domain in self._last_crawl:
                time_since_last = (now - self._last_crawl[domain]).total_seconds()
                if time_since_last < self._min_delay:
                    logger.info(f"Rate limited for domain {domain}")
                    return False
            
            self._last_crawl[domain] = now
            return True
            
        except Exception as e:
            logger.error(f"Error in rate limiter: {e}")
            return True  # Allow crawling if rate limiting fails


# Convenience functions
async def crawl_url(url: str, 
                   extract_entities: bool = True,
                   storage_client=None) -> CrawlJobResponse:
    """Convenience function to crawl a single URL"""
    manager = CrawlJobManager(storage_client)
    
    request = CrawlJobRequest(
        url=url,
        extract_entities=extract_entities,
        politeness_delay=1.0
    )
    
    return await manager.create_and_execute_job(request)


async def crawl_multiple_urls(urls: List[str], 
                            concurrent_limit: int = 3,
                            storage_client=None) -> List[CrawlJobResponse]:
    """Crawl multiple URLs with concurrency control"""
    manager = CrawlJobManager(storage_client)
    
    async def crawl_single(url: str) -> CrawlJobResponse:
        request = CrawlJobRequest(url=url, politeness_delay=2.0)  # Higher delay for batch
        return await manager.create_and_execute_job(request)
    
    # Use semaphore to limit concurrency
    semaphore = asyncio.Semaphore(concurrent_limit)
    
    async def limited_crawl(url: str) -> CrawlJobResponse:
        async with semaphore:
            return await crawl_single(url)
    
    tasks = [limited_crawl(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to failed job responses
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed_job = CrawlJobResponse(
                job_id=f"failed_{i}",
                url=urls[i],
                status=CrawlStatus.FAILED,
                error=str(result),
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
            final_results.append(failed_job)
        else:
            final_results.append(result)
    
    return final_results