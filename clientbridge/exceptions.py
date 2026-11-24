"""Exceptions raised by the clientbridge package."""


class ClientBridgeError(Exception):
    """Base class for every error raised by this package."""


class NetworkError(ClientBridgeError):
    """The HTTP request could not be completed."""


class APIError(ClientBridgeError):
    """The API returned an unsuccessful or unusable response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(APIError):
    """The API key is missing or invalid."""


class RateLimitError(APIError):
    """The API rejected the request because the rate limit was exceeded."""


class ServerError(APIError):
    """The API server failed to process the request."""
