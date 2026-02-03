"""Wikipedia content source.

Fetches articles via the Wikipedia API for sandwich ingredient discovery.

Reference: SPEC.md Section 3.2.1; PROMPTS.md Prompt 8
"""

import logging
from typing import Optional

import httpx

from sandwich.sources.base import ContentSource, RateLimiter, SourceResult

logger = logging.getLogger(__name__)

WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1"
WIKIPEDIA_ACTION_API = "https://en.wikipedia.org/w/api.php"


class WikipediaSource(ContentSource):
    """Wikipedia content source using the REST and Action APIs."""

    name = "wikipedia"
    tier = 1

    def __init__(self, max_per_minute: int = 200):
        self.rate_limiter = RateLimiter(max_per_minute)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "SANDWICH-Bot/1.0 (https://github.com/MLenaBleile/reuben; sandwich research project)",
                    "Api-User-Agent": "SANDWICH-Bot/1.0 (https://github.com/MLenaBleile/reuben; sandwich research project)",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch_random(self) -> SourceResult:
        """Fetch a random Wikipedia article.

        Uses the Action API with list=random to get a random article title,
        then fetches its content via the REST API.
        """
        self.rate_limiter.wait_if_needed()
        client = await self._get_client()

        # Get a random article title
        params = {
            "action": "query",
            "list": "random",
            "rnnamespace": 0,
            "rnlimit": 1,
            "format": "json",
        }
        resp = await client.get(WIKIPEDIA_ACTION_API, params=params)
        resp.raise_for_status()
        data = resp.json()
        title = data["query"]["random"][0]["title"]

        return await self._fetch_article(title)

    async def fetch(self, query: Optional[str] = None) -> SourceResult:
        """Search Wikipedia and fetch the top result.

        Args:
            query: Search query string.

        Returns:
            SourceResult with article content.
        """
        if query is None:
            return await self.fetch_random()

        self.rate_limiter.wait_if_needed()
        client = await self._get_client()

        # Truncate long queries — Wikipedia rejects overly long search strings
        if len(query) > 100:
            query = " ".join(query.split()[:10])

        # Search for articles
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
            "format": "json",
        }
        resp = await client.get(WIKIPEDIA_ACTION_API, params=params)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("query", {}).get("search", [])
        if not results:
            return SourceResult(
                content="",
                title=None,
                url=None,
                content_type="text",
                metadata={"query": query, "error": "no_results"},
            )

        title = results[0]["title"]
        return await self._fetch_article(title)

    async def _fetch_article(self, title: str) -> SourceResult:
        """Fetch article content by title using the REST API."""
        self.rate_limiter.wait_if_needed()
        client = await self._get_client()

        # URL-encode the title for the REST API
        encoded_title = title.replace(" ", "_")
        url = f"{WIKIPEDIA_API_URL}/page/summary/{encoded_title}"

        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError:
            logger.warning("Failed to fetch summary for '%s', trying extract", title)
            return await self._fetch_extract(title)

        extract = data.get("extract", "")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

        # If extract is too short, try the full extract
        if len(extract) < 200:
            return await self._fetch_extract(title)

        return SourceResult(
            content=extract,
            title=data.get("title", title),
            url=page_url or f"https://en.wikipedia.org/wiki/{encoded_title}",
            content_type="text",
            metadata={"source": "wikipedia", "description": data.get("description", "")},
        )

    async def _fetch_extract(self, title: str) -> SourceResult:
        """Fetch full text extract via the Action API (fallback)."""
        self.rate_limiter.wait_if_needed()
        client = await self._get_client()

        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "explaintext": True,
            "exlimit": 1,
            "format": "json",
        }
        resp = await client.get(WIKIPEDIA_ACTION_API, params=params)
        resp.raise_for_status()
        data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})
        extract = page.get("extract", "")
        encoded_title = title.replace(" ", "_")

        return SourceResult(
            content=extract,
            title=page.get("title", title),
            url=f"https://en.wikipedia.org/wiki/{encoded_title}",
            content_type="text",
            metadata={"source": "wikipedia", "method": "extract"},
        )
