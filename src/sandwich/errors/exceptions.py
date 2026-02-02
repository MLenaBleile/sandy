"""Error taxonomy for the SANDWICH system.

Reference: SPEC.md Sections 6.1, 6.2
"""


class SandwichError(Exception):
    """Base exception for all SANDWICH system errors."""

    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message)
        self.context = context or {}


class RetryableError(SandwichError):
    """Errors that may succeed on retry (rate limits, network, timeout).

    These should be caught by the retry wrapper and retried with
    exponential backoff.
    """

    def __init__(
        self,
        message: str,
        reason: str = "unknown",
        context: dict | None = None,
    ):
        super().__init__(message, context)
        self.reason = reason  # 'rate_limit', 'network', 'timeout'


class ContentError(SandwichError):
    """Errors related to content quality or suitability.

    These indicate the content cannot produce a sandwich and the agent
    should move on to the next piece of content.
    """

    def __init__(
        self,
        message: str,
        reason: str = "unknown",
        context: dict | None = None,
    ):
        super().__init__(message, context)
        self.reason = reason  # 'too_short', 'non_english', 'low_quality', 'duplicate'


class ParseError(SandwichError):
    """Errors from parsing LLM output (malformed JSON, missing fields).

    May be retried with a stricter prompt via parse_with_recovery.
    """

    def __init__(
        self,
        message: str,
        raw_output: str | None = None,
        context: dict | None = None,
    ):
        super().__init__(message, context)
        self.raw_output = raw_output


class FatalError(SandwichError):
    """Unrecoverable errors that should terminate the session.

    Examples: database down, configuration error, authentication failure.
    """

    def __init__(
        self,
        message: str,
        reason: str = "unknown",
        context: dict | None = None,
    ):
        super().__init__(message, context)
        self.reason = reason  # 'database_down', 'config_error', 'auth_error'
