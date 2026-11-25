"""Exception raised by the API wrapper."""


class ApiClientError(Exception):
    """The API could not be reached or returned an unusable response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
