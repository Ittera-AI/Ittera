"""
Retry utilities with exponential backoff for external API calls.

Uses tenacity for robust retry logic with configurable:
- Number of attempts
- Wait time between retries (exponential backoff)
- Retryable exceptions
- Stop conditions
"""

import logging
from functools import wraps
from typing import Callable, Optional, Tuple, Type, Union

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    after_log,
)

logger = logging.getLogger("iterra.retry")


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception], None]] = None,
):
    """
    Decorator that adds exponential backoff retry logic to a function.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        min_wait: Minimum wait time between retries in seconds (default: 1)
        max_wait: Maximum wait time between retries in seconds (default: 10)
        retryable_exceptions: Tuple of exception types to retry on (default: all Exceptions)
        on_retry: Optional callback function called before each retry with the exception

    Example:
        @with_retry(
            max_attempts=3,
            retryable_exceptions=(ConnectionError, TimeoutError),
        )
        def fetch_data():
            # This will retry on ConnectionError or TimeoutError
            return make_api_call()
    """
    def decorator(func: Callable) -> Callable:
        @retry(
            retry=retry_if_exception_type(retryable_exceptions),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True,  # Re-raise the original exception after all retries fail
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except retryable_exceptions as exc:
                if on_retry:
                    on_retry(exc)
                raise

        return wrapper

    return decorator


# Pre-configured retry decorators for common use cases

def drive_api_retry(max_attempts: int = 3):
    """
    Retry decorator specifically for Google Drive API calls.

    Retries on:
    - Connection errors (network issues)
    - Timeout errors
    - 5xx server errors
    - Rate limit errors (429)

    Uses exponential backoff with jitter.
    """
    from googleapiclient.errors import HttpError
    from google.auth.exceptions import RefreshError, TransportError
    import socket
    import ssl

    return with_retry(
        max_attempts=max_attempts,
        min_wait=1,
        max_wait=30,
        retryable_exceptions=(
            HttpError,  # Google API HTTP errors
            RefreshError,  # Token refresh errors
            TransportError,  # Transport-level errors
            ConnectionError,
            TimeoutError,
            socket.error,
            ssl.SSLError,
        ),
    )


# Custom retry condition functions

def is_transient_error(exc: Exception) -> bool:
    """
    Check if an exception is likely transient and should be retried.

    Args:
        exc: The exception to check

    Returns:
        True if the error is likely transient
    """
    from googleapiclient.errors import HttpError
    from http import HTTPStatus

    if isinstance(exc, HttpError):
        # Retry on 5xx errors, 429 (rate limit), and 403 (sometimes transient)
        if exc.resp.status >= 500:
            return True
        if exc.resp.status == HTTPStatus.TOO_MANY_REQUESTS:  # 429
            return True
        # 403 can be rate limit or permission - check error details
        if exc.resp.status == HTTPStatus.FORBIDDEN:
            # Check if it's a rate limit error
            error_details = exc.error_details if hasattr(exc, 'error_details') else []
            for detail in error_details:
                reason = detail.get('reason', '') if isinstance(detail, dict) else ''
                if 'rate' in reason.lower() or 'limit' in reason.lower():
                    return True
        return False

    # Connection errors are generally transient
    import socket
    import ssl
    if isinstance(exc, (ConnectionError, TimeoutError, socket.error, ssl.SSLError)):
        return True

    return False


# Retry statistics tracking

class RetryStats:
    """Track retry statistics for monitoring and debugging."""

    def __init__(self):
        self.attempts = 0
        self.successes = 0
        self.failures = 0
        self.total_wait_time = 0.0

    def record_attempt(self, wait_time: float = 0):
        self.attempts += 1
        self.total_wait_time += wait_time

    def record_success(self):
        self.successes += 1

    def record_failure(self):
        self.failures += 1

    def to_dict(self) -> dict:
        return {
            "attempts": self.attempts,
            "successes": self.successes,
            "failures": self.failures,
            "total_wait_time_seconds": self.total_wait_time,
            "success_rate": self.successes / max(self.attempts, 1),
        }
