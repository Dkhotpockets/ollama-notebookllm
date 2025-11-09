"""
Topic Discovery Agent for automatic content discovery

This agent searches the web for high-quality learning resources on a given topic
and returns a ranked list of URLs for crawling and processing.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredResource:
    """Represents a discovered learning resource"""
    url: str
    title: str
    description: str
    source_type: str  # 'official_docs', 'tutorial', 'github', 'educational', 'blog', 'other'
    priority_score: float  # Higher is better (0.0 - 1.0)

    def __repr__(self):
        return f"DiscoveredResource(url={self.url}, title={self.title}, priority={self.priority_score:.2f})"


class TopicDiscoveryAgent:
    """
    Intelligent agent for discovering high-quality learning resources on a topic.

    Uses DuckDuckGo search (no API key required) to find resources,
    then ranks them based on source quality and relevance.
    """

    # High-authority domains for different content types
    OFFICIAL_DOCS_DOMAINS = {
        'docs.python.org', 'developer.mozilla.org', 'docs.microsoft.com',
        'docs.oracle.com', 'golang.org', 'rust-lang.org', 'kotlinlang.org',
        'docs.rs', 'reactjs.org', 'vuejs.org', 'angular.io', 'svelte.dev',
        'nodejs.org', 'docs.docker.com', 'kubernetes.io', 'docs.aws.amazon.com',
        'cloud.google.com', 'docs.github.com', 'typescriptlang.org'
    }

    EDUCATIONAL_PLATFORMS = {
        'w3schools.com', 'freecodecamp.org', 'codecademy.com',
        'khanacademy.org', 'coursera.org', 'udacity.com', 'edx.org',
        'realpython.com', 'learnpython.org', 'learn.microsoft.com',
        'developers.google.com', 'tutorialspoint.com', 'geeksforgeeks.org'
    }

    QUALITY_BLOG_DOMAINS = {
        'medium.com', 'dev.to', 'hashnode.dev', 'css-tricks.com',
        'smashingmagazine.com', 'a11y.com', 'martinfowler.com',
        'blog.cleancoder.com', 'joelonsoftware.com'
    }

    GITHUB_DOMAINS = {'github.com', 'gitlab.com', 'bitbucket.org'}

    def __init__(self, max_results_per_query: int = 10, enable_caching: bool = True):
        """
        Initialize the topic discovery agent.

        Args:
            max_results_per_query: Maximum results to fetch per search query
            enable_caching: Whether to cache search results to avoid re-searching
        """
        self.max_results_per_query = max_results_per_query
        self.enable_caching = enable_caching
        self._cache: Dict[str, List[DiscoveredResource]] = {}

    async def discover_resources(self, topic: str, max_resources: int = 20) -> List[DiscoveredResource]:
        """
        Discover high-quality learning resources for a given topic.

        Args:
            topic: The topic to search for (e.g., "TypeScript", "machine learning")
            max_resources: Maximum number of resources to return

        Returns:
            List of DiscoveredResource objects, sorted by priority (highest first)
        """
        # Check cache first
        cache_key = f"{topic}:{max_resources}"
        if self.enable_caching and cache_key in self._cache:
            logger.info(f"Using cached results for topic: {topic}")
            return self._cache[cache_key]

        logger.info(f"Discovering resources for topic: {topic}")

        # Build search queries for different resource types
        search_queries = self._build_search_queries(topic)

        # Execute searches in parallel
        all_resources = []
        search_tasks = [self._search_duckduckgo(query) for query in search_queries]
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Collect all discovered resources
        for results in search_results:
            if isinstance(results, Exception):
                logger.error(f"Search error: {results}")
                continue
            all_resources.extend(results)

        # Deduplicate by URL
        unique_resources = self._deduplicate_resources(all_resources)

        # Rank and sort by priority
        ranked_resources = sorted(unique_resources, key=lambda r: r.priority_score, reverse=True)

        # Limit to max_resources
        final_resources = ranked_resources[:max_resources]

        # Cache results
        if self.enable_caching:
            self._cache[cache_key] = final_resources

        logger.info(f"Discovered {len(final_resources)} resources for topic: {topic}")
        return final_resources

    def _build_search_queries(self, topic: str) -> List[str]:
        """
        Build multiple search queries to find different types of resources.

        Args:
            topic: The base topic

        Returns:
            List of search query strings
        """
        queries = [
            f"{topic} official documentation",
            f"{topic} tutorial beginner guide",
            f"{topic} getting started guide",
            f"learn {topic} step by step",
            f"{topic} best practices examples",
            f"{topic} github repository tutorial"
        ]
        return queries

    async def _search_duckduckgo(self, query: str) -> List[DiscoveredResource]:
        """
        Search DuckDuckGo for results using multi-provider approach.

        Args:
            query: Search query string

        Returns:
            List of DiscoveredResource objects
        """
        try:
            from .search_providers import multi_provider_search

            # Use multi-provider search (tries multiple methods)
            search_results = await multi_provider_search(query, self.max_results_per_query)

            resources = []
            for result in search_results:
                if not result.url or not result.title:
                    continue

                # Classify and score the resource
                source_type = self._classify_source(result.url)
                priority_score = self._calculate_priority_score(
                    result.url, result.title, result.description, source_type
                )

                resource = DiscoveredResource(
                    url=result.url,
                    title=result.title,
                    description=result.description,
                    source_type=source_type,
                    priority_score=priority_score
                )
                resources.append(resource)

            return resources

        except ImportError as e:
            logger.error(f"Search providers not available: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def _classify_source(self, url: str) -> str:
        """
        Classify the source type based on URL.

        Args:
            url: Resource URL

        Returns:
            Source type string
        """
        try:
            domain = urlparse(url).netloc.lower()
            # Remove www. prefix
            domain = domain.replace('www.', '')

            if any(official in domain for official in self.OFFICIAL_DOCS_DOMAINS):
                return 'official_docs'
            elif any(edu in domain for edu in self.EDUCATIONAL_PLATFORMS):
                return 'educational'
            elif any(gh in domain for gh in self.GITHUB_DOMAINS):
                return 'github'
            elif any(blog in domain for blog in self.QUALITY_BLOG_DOMAINS):
                return 'blog'
            else:
                return 'other'
        except Exception as e:
            logger.warning(f"Error classifying source {url}: {e}")
            return 'other'

    def _calculate_priority_score(self, url: str, title: str, description: str, source_type: str) -> float:
        """
        Calculate priority score for a resource (0.0 - 1.0, higher is better).

        Factors:
        - Source type (official docs highest, other lowest)
        - URL structure (shorter paths often better)
        - Title/description quality indicators

        Args:
            url: Resource URL
            title: Resource title
            description: Resource description
            source_type: Classified source type

        Returns:
            Priority score between 0.0 and 1.0
        """
        score = 0.5  # Base score

        # Source type bonus
        source_type_scores = {
            'official_docs': 0.4,
            'educational': 0.3,
            'github': 0.2,
            'blog': 0.15,
            'other': 0.0
        }
        score += source_type_scores.get(source_type, 0.0)

        # URL structure bonus (prefer cleaner URLs)
        try:
            path_depth = len(urlparse(url).path.strip('/').split('/'))
            if path_depth <= 2:
                score += 0.1
            elif path_depth <= 4:
                score += 0.05
        except:
            pass

        # Quality indicators in title/description
        quality_keywords = [
            'official', 'documentation', 'guide', 'tutorial', 'introduction',
            'getting started', 'learn', 'course', 'reference', 'handbook',
            'comprehensive', 'complete', 'beginner', 'fundamentals'
        ]

        text = (title + ' ' + description).lower()
        keyword_matches = sum(1 for keyword in quality_keywords if keyword in text)
        score += min(keyword_matches * 0.02, 0.1)  # Cap at 0.1

        # Penalize very long URLs (often low-quality)
        if len(url) > 150:
            score -= 0.1

        # Penalize certain spam indicators
        spam_indicators = ['?ref=', 'affiliate', 'ad.', 'ads.', 'popup']
        if any(indicator in url.lower() for indicator in spam_indicators):
            score -= 0.3

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, score))

    def _deduplicate_resources(self, resources: List[DiscoveredResource]) -> List[DiscoveredResource]:
        """
        Remove duplicate resources based on URL.

        If duplicates exist, keep the one with the highest priority score.

        Args:
            resources: List of resources

        Returns:
            Deduplicated list of resources
        """
        url_to_resource: Dict[str, DiscoveredResource] = {}

        for resource in resources:
            if resource.url not in url_to_resource:
                url_to_resource[resource.url] = resource
            else:
                # Keep the one with higher priority
                existing = url_to_resource[resource.url]
                if resource.priority_score > existing.priority_score:
                    url_to_resource[resource.url] = resource

        return list(url_to_resource.values())

    def get_resources_by_type(self, resources: List[DiscoveredResource], source_type: str) -> List[DiscoveredResource]:
        """
        Filter resources by source type.

        Args:
            resources: List of resources
            source_type: Type to filter by

        Returns:
            Filtered list of resources
        """
        return [r for r in resources if r.source_type == source_type]

    def clear_cache(self):
        """Clear the resource cache."""
        self._cache.clear()
        logger.info("Resource cache cleared")


# Convenience function for quick usage
async def discover_topic_resources(topic: str, max_resources: int = 20) -> List[DiscoveredResource]:
    """
    Convenience function to discover resources for a topic.

    Args:
        topic: Topic to search for
        max_resources: Maximum resources to return

    Returns:
        List of discovered resources
    """
    agent = TopicDiscoveryAgent()
    return await agent.discover_resources(topic, max_resources)
