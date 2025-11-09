"""
Alternative search providers for topic discovery
Provides fallback options when primary search fails
"""

import logging
import asyncio
from typing import List, Dict, Any
import urllib.parse
import urllib.request
import json

logger = logging.getLogger(__name__)


class SearchResult:
    """Simple search result container"""
    def __init__(self, title: str, url: str, description: str):
        self.title = title
        self.url = url
        self.description = description


async def search_with_ddgs(query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Search using ddgs library (primary method)
    """
    try:
        from ddgs import DDGS

        def _search():
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                return results
            except Exception as e:
                logger.warning(f"DDGS search failed: {e}")
                return []

        loop = asyncio.get_event_loop()
        raw_results = await loop.run_in_executor(None, _search)

        search_results = []
        for r in raw_results:
            search_results.append(SearchResult(
                title=r.get('title', ''),
                url=r.get('href', ''),
                description=r.get('body', '')
            ))

        return search_results

    except ImportError:
        logger.warning("ddgs library not available")
        return []
    except Exception as e:
        logger.error(f"DDGS search error: {e}")
        return []


async def search_with_duckduckgo_html(query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Search using DuckDuckGo HTML scraping (fallback method)
    More reliable but slower
    """
    try:
        import re
        from html.parser import HTMLParser

        class DuckDuckGoHTMLParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self.current_result = {}
                self.in_title = False
                self.in_snippet = False

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)

                # Look for result links
                if tag == 'a' and attrs_dict.get('class', '').startswith('result'):
                    href = attrs_dict.get('href', '')
                    if href and not href.startswith('/'):
                        self.current_result = {'url': href}
                        self.in_title = True

                # Look for snippets
                if tag == 'div' and 'result__snippet' in attrs_dict.get('class', ''):
                    self.in_snippet = True

            def handle_data(self, data):
                if self.in_title and 'url' in self.current_result:
                    self.current_result['title'] = data.strip()
                    self.in_title = False
                elif self.in_snippet:
                    self.current_result['description'] = data.strip()
                    self.in_snippet = False
                    if len(self.current_result) == 3:  # Has url, title, and description
                        self.results.append(SearchResult(**self.current_result))
                        self.current_result = {}

        # Encode query
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        # Fetch results
        def _fetch():
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('utf-8')

        loop = asyncio.get_event_loop()
        html = await loop.run_in_executor(None, _fetch)

        # Parse HTML
        parser = DuckDuckGoHTMLParser()
        parser.feed(html)

        return parser.results[:max_results]

    except Exception as e:
        logger.error(f"DuckDuckGo HTML search error: {e}")
        return []


async def search_with_hardcoded_sources(query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Fallback: Use hardcoded high-quality sources (last resort)
    Searches within known documentation sites
    """
    topic = query.lower().split()[0]  # Get first word as topic

    # Hardcoded documentation sources
    sources = {
        'python': [
            ('Python Official Documentation', 'https://docs.python.org/3/', 'Official Python documentation'),
            ('Python Tutorial', 'https://docs.python.org/3/tutorial/', 'Python official tutorial'),
            ('Real Python', 'https://realpython.com/', 'Python tutorials and articles'),
        ],
        'javascript': [
            ('MDN JavaScript', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript', 'MDN JavaScript documentation'),
            ('JavaScript.info', 'https://javascript.info/', 'Modern JavaScript tutorial'),
        ],
        'typescript': [
            ('TypeScript Docs', 'https://www.typescriptlang.org/docs/', 'Official TypeScript documentation'),
            ('TypeScript Handbook', 'https://www.typescriptlang.org/docs/handbook/intro.html', 'TypeScript handbook'),
        ],
        'react': [
            ('React Docs', 'https://react.dev/', 'Official React documentation'),
            ('React Tutorial', 'https://react.dev/learn', 'Learn React'),
        ],
        'docker': [
            ('Docker Docs', 'https://docs.docker.com/', 'Official Docker documentation'),
            ('Docker Get Started', 'https://docs.docker.com/get-started/', 'Docker getting started guide'),
        ],
        'kubernetes': [
            ('Kubernetes Docs', 'https://kubernetes.io/docs/', 'Official Kubernetes documentation'),
            ('Kubernetes Basics', 'https://kubernetes.io/docs/tutorials/kubernetes-basics/', 'Kubernetes basics tutorial'),
        ],
    }

    # Find matching sources
    results = []
    for key, source_list in sources.items():
        if key in topic or topic in key:
            for title, url, description in source_list[:max_results]:
                results.append(SearchResult(title, url, description))

    # If no matches, return popular learning sites
    if not results:
        results = [
            SearchResult(
                f'{topic.title()} on W3Schools',
                f'https://www.w3schools.com/{topic}/',
                f'W3Schools {topic} tutorial'
            ),
            SearchResult(
                f'{topic.title()} on MDN',
                f'https://developer.mozilla.org/en-US/search?q={urllib.parse.quote(topic)}',
                f'MDN resources for {topic}'
            ),
        ]

    return results[:max_results]


async def multi_provider_search(query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Try multiple search providers in order of preference
    Returns first successful result
    """
    providers = [
        ("DDGS", search_with_ddgs),
        ("DuckDuckGo HTML", search_with_duckduckgo_html),
        ("Hardcoded Sources", search_with_hardcoded_sources),
    ]

    for provider_name, provider_func in providers:
        try:
            logger.info(f"Trying search provider: {provider_name}")
            results = await provider_func(query, max_results)

            if results and len(results) > 0:
                logger.info(f"✅ {provider_name} returned {len(results)} results")
                return results
            else:
                logger.warning(f"⚠️  {provider_name} returned 0 results")

        except Exception as e:
            logger.error(f"❌ {provider_name} failed: {e}")

    logger.error("All search providers failed")
    return []
