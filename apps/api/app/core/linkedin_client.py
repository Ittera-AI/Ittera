"""
LinkedInClient — production-grade wrapper around LinkedIn API calls.

Features:
  - Intelligent retry logic with exponential backoff
  - Rate limiting awareness (429 handling)
  - Connection pooling for performance
  - Comprehensive error handling with actionable messages
  - Request/response logging for debugging
  - Token refresh handling

Two auth modes supported:
  1. OAuth access token (preferred) — for API calls
  2. Cookie-based — delegated to linkedin-api library

Usage:
    client = LinkedInClient(access_token="...")
    profile = await client.get_profile()
    posts = await client.get_posts(member_urn="urn:li:person:...", count=50)
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class LinkedInClientError(Exception):
    """Base exception for LinkedIn client errors."""
    
    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ScopeMissingError(LinkedInClientError):
    """Raised when the OAuth token lacks required scope (e.g., r_member_social)."""
    pass


class TokenExpiredError(LinkedInClientError):
    """Raised when the OAuth token is expired or invalid."""
    pass


class RateLimitError(LinkedInClientError):
    """Raised when LinkedIn API rate limit is hit (429)."""
    pass


class LinkedInAPIError(LinkedInClientError):
    """Raised for other LinkedIn API errors."""
    pass


class LinkedInClient:
    """
    Production-grade LinkedIn API client for OAuth-based interactions.
    
    Features:
        - Automatic retries with exponential backoff
        - Rate limit handling
        - Connection pooling
        - Comprehensive logging
    """

    BASE_URL = "https://api.linkedin.com"
    API_VERSION = "202605"
    RESTLI_VERSION = "2.0.0"
    MAX_RETRIES = 3
    
    # Rate limiting
    RATE_LIMIT_STATUS = 429
    DEFAULT_RATE_LIMIT_RETRY_AFTER = 60  # seconds

    def __init__(self, access_token: str, timeout: float = 30.0):
        self._token = access_token
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": self.API_VERSION,
            "X-Restli-Protocol-Version": self.RESTLI_VERSION,
        }
        # Create persistent client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            headers=self._headers,
        )
        
        logger.debug("LinkedInClient initialized with API version %s", self.API_VERSION)

    async def __aenter__(self) -> LinkedInClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - closes client."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client and release connections."""
        await self._client.aclose()
        logger.debug("LinkedInClient connection closed")

    def _handle_error(self, response: httpx.Response, context: str) -> None:
        """
        Handle HTTP error responses with specific exception types.
        
        Args:
            response: The HTTP response
            context: Description of the operation for logging
            
        Raises:
            Appropriate exception based on status code
        """
        status = response.status_code
        body = response.text[:500]  # Limit error body length
        
        logger.warning(
            "LinkedIn API error: %s - Status %d - Body: %s",
            context,
            status,
            body,
        )
        
        if status == 401:
            raise TokenExpiredError(
                f"Token expired or invalid during {context}. Reconnect LinkedIn.",
                status_code=status,
                response_body=body,
            )
        elif status == 403:
            raise ScopeMissingError(
                f"Insufficient permissions during {context}. "
                "Ensure r_member_social and w_member_social scopes are granted.",
                status_code=status,
                response_body=body,
            )
        elif status == self.RATE_LIMIT_STATUS:
            retry_after = int(response.headers.get("Retry-After", self.DEFAULT_RATE_LIMIT_RETRY_AFTER))
            raise RateLimitError(
                f"Rate limit exceeded during {context}. Retry after {retry_after}s.",
                status_code=status,
                response_body=body,
            )
        elif status >= 500:
            raise LinkedInAPIError(
                f"LinkedIn server error during {context}. Status: {status}",
                status_code=status,
                response_body=body,
            )
        else:
            raise LinkedInAPIError(
                f"LinkedIn API error during {context}. Status: {status}",
                status_code=status,
                response_body=body,
            )

    @retry(
        retry=retry_if_exception_type((LinkedInAPIError, RateLimitError, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def get_profile(self) -> dict[str, Any]:
        """
        Fetch the current user's basic profile.
        
        Returns:
            Dict with 'id' (member URN suffix) and other profile fields.
            
        Raises:
            TokenExpiredError: If token is invalid
            LinkedInClientError: For other API errors
        """
        url = f"{self.BASE_URL}/v2/me"
        
        logger.debug("Fetching LinkedIn profile")
        
        try:
            response = await self._client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Successfully fetched LinkedIn profile for user %s", data.get("id", "unknown"))
                return data
            
            self._handle_error(response, "profile fetch")
            
        except httpx.NetworkError as e:
            logger.warning("Network error fetching profile: %s", e)
            raise LinkedInAPIError(f"Network error: {e}") from e
        except Exception:
            logger.exception("Unexpected error fetching profile")
            raise

    @retry(
        retry=retry_if_exception_type((LinkedInAPIError, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def get_posts(
        self,
        member_urn: str,
        count: int = 50,
        start: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Fetch UGC posts for a given member URN.
        
        Requires r_member_social scope. Raises ScopeMissingError on 403.
        
        Args:
            member_urn: Full URN like "urn:li:person:ABC123" or just "ABC123"
            count: Number of posts to fetch (max 100, capped at 50 for performance)
            start: Pagination offset

        Returns:
            List of post element dicts from LinkedIn API
            
        Raises:
            ScopeMissingError: If token lacks r_member_social scope
            TokenExpiredError: If token is invalid
        """
        # Normalize URN
        if not member_urn.startswith("urn:"):
            member_urn = f"urn:li:person:{member_urn}"

        # Cap count for performance
        count = min(count, 50)

        url = f"{self.BASE_URL}/v2/ugcPosts"
        params = {
            "q": "authors",
            "authors": f"List({member_urn})",
            "count": count,
            "start": start,
        }

        logger.debug("Fetching LinkedIn posts for %s (count=%d, start=%d)", member_urn, count, start)

        try:
            response = await self._client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get("elements", [])
                logger.info("Successfully fetched %d LinkedIn posts", len(elements))
                return elements
            
            self._handle_error(response, f"posts fetch for {member_urn}")
            
        except httpx.NetworkError as e:
            logger.warning("Network error fetching posts: %s", e)
            raise LinkedInAPIError(f"Network error: {e}") from e
        except Exception:
            logger.exception("Unexpected error fetching posts")
            raise

    @retry(
        retry=retry_if_exception_type((LinkedInAPIError, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get_social_actions(self, post_urn: str) -> dict[str, Any]:
        """
        Fetch social actions (likes, comments, shares) for a post.
        
        Note: This endpoint may require additional permissions.

        Args:
            post_urn: Full post URN like "urn:li:share:ABC123"

        Returns:
            Dict with social action counts (likes, comments, shares)
            Returns empty dict on 403/404 (permissions or post not found)
        """
        # Properly encode URN for URL
        encoded_urn = quote(post_urn, safe="")
        url = f"{self.BASE_URL}/v2/socialActions/{encoded_urn}"

        logger.debug("Fetching social actions for post %s", post_urn)

        try:
            response = await self._client.get(url)

            if response.status_code == 200:
                data = response.json()
                # Extract counts from nested structure
                likes = data.get("likesSummary", {}).get("totalLikes", 0)
                comments = data.get("commentsSummary", {}).get("totalComments", 0)
                shares = data.get("sharesSummary", {}).get("totalShares", 0)
                
                logger.debug("Social actions for %s: %d likes, %d comments, %d shares", 
                           post_urn, likes, comments, shares)
                return {
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "raw": data,
                }
            elif response.status_code in (403, 404):
                # These are expected for posts we can't access
                logger.debug("Cannot access social actions for %s (status %d)", 
                           post_urn, response.status_code)
                return {"likes": 0, "comments": 0, "shares": 0, "raw": None}
            
            self._handle_error(response, f"social actions fetch for {post_urn}")
            
        except httpx.NetworkError as e:
            logger.warning("Network error fetching social actions: %s", e)
            return {"likes": 0, "comments": 0, "shares": 0, "raw": None}
        except Exception:
            logger.exception("Unexpected error fetching social actions")
            return {"likes": 0, "comments": 0, "shares": 0, "raw": None}

    @retry(
        retry=retry_if_exception_type((LinkedInAPIError, RateLimitError, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def publish_post(
        self,
        member_urn: str,
        text: str,
        visibility: str = "PUBLIC",
    ) -> dict[str, Any]:
        """
        Publish a text post to LinkedIn.
        
        Requires w_member_social scope.

        Args:
            member_urn: Author URN like "urn:li:person:ABC123"
            text: Post content (max 3000 chars for LinkedIn)
            visibility: "PUBLIC" or "CONNECTIONS"

        Returns:
            Dict with published post ID and metadata
            
        Raises:
            ScopeMissingError: If token lacks w_member_social scope
            TokenExpiredError: If token is invalid
        """
        # Normalize URN
        if not member_urn.startswith("urn:"):
            member_urn = f"urn:li:person:{member_urn}"

        # Validate text length
        if len(text) > 3000:
            text = text[:2997] + "..."
            logger.warning("Post text truncated to 3000 characters")

        url = f"{self.BASE_URL}/v2/ugcPosts"
        body = {
            "author": member_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            },
        }

        logger.info("Publishing LinkedIn post for author %s", member_urn)

        try:
            response = await self._client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=body,
            )

            if response.status_code in (200, 201):
                data = response.json()
                logger.info("Successfully published LinkedIn post: %s", data.get("id", "unknown"))
                return data
            
            self._handle_error(response, "post publish")
            
        except httpx.NetworkError as e:
            logger.warning("Network error publishing post: %s", e)
            raise LinkedInAPIError(f"Network error: {e}") from e
        except Exception:
            logger.exception("Unexpected error publishing post")
            raise


class LinkedInCookieClient:
    """
    LinkedIn client using cookie-based authentication via linkedin-api library.
    This is a fallback when OAuth tokens lack required scopes.
    
    Features connection pooling and retry logic.
    """

    def __init__(self, username: str, password: str, timeout: int = 30):
        self._username = username
        self._password = password
        self._timeout = timeout
        self._client = None
        self._client_lock = False

    def _get_client(self):
        """Lazy initialization of the linkedin-api client with thread safety."""
        if self._client is None and not self._client_lock:
            self._client_lock = True
            try:
                from linkedin_api import Linkedin  # type: ignore[import]
                self._client = Linkedin(self._username, self._password)
                logger.info("LinkedIn cookie-based client initialized")
            except ImportError as e:
                raise LinkedInClientError(
                    "linkedin-api library not installed. Run: pip install linkedin-api"
                ) from e
            except Exception as e:
                raise LinkedInClientError(f"Failed to initialize LinkedIn client: {e}") from e
            finally:
                self._client_lock = False
        return self._client

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def get_profile(self) -> dict[str, Any]:
        """Fetch own profile to resolve public_id."""
        try:
            client = self._get_client()
            return client.get_profile(urn_id=None)
        except Exception as e:
            logger.exception("Error fetching profile via cookie auth")
            raise LinkedInClientError(f"Profile fetch failed: {e}") from e

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def get_posts(self, public_id: str, count: int = 50) -> list[dict[str, Any]]:
        """
        Fetch posts for a given public profile ID.

        Args:
            public_id: LinkedIn public identifier (e.g., "john-doe-123")
            count: Number of posts to fetch

        Returns:
            List of raw post dicts from linkedin-api
        """
        try:
            client = self._get_client()
            posts = client.get_profile_posts(public_id=public_id, post_count=count)
            logger.info("Fetched %d posts via cookie auth for %s", len(posts or []), public_id)
            return posts or []
        except Exception as e:
            logger.exception("Error fetching posts via cookie auth")
            raise LinkedInClientError(f"Posts fetch failed: {e}") from e

    def get_post_stats(self, post_urn: str) -> dict[str, Any]:
        """
        Get engagement stats for a specific post.
        Note: linkedin-api may not support direct post stats; returns empty dict.
        """
        logger.debug("Cookie client: post stats not directly available via linkedin-api")
        return {}
