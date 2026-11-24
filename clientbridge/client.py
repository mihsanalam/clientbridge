"""HTTP client for the OpenWeatherMap current weather endpoint."""

import time
from dataclasses import dataclass
from typing import Optional

import requests

from .exceptions import (
    APIError,
    AuthenticationError,
    ClientBridgeError,
    NetworkError,
    RateLimitError,
    ServerError,
)

DEFAULT_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
VALID_UNITS = ("metric", "imperial", "standard")


@dataclass(frozen=True)
class Weather:
    """Current conditions at a single location."""

    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    description: str
    units: str


class WeatherClient:
    """Fetch current weather reports from OpenWeatherMap."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        if retries < 0:
            raise ValueError("retries must not be negative")
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.session = session if session is not None else requests.Session()

    def get_weather(self, city: str, units: str = "metric") -> Weather:
        """Return the current weather for ``city`` in the requested units."""
        if units not in VALID_UNITS:
            raise ValueError(f"units must be one of: {', '.join(VALID_UNITS)}")
        if not city.strip():
            raise ValueError("city must not be empty")

        params = {"q": city, "appid": self.api_key, "units": units}
        payload = self._get(params)
        return self._parse(payload, units)

    def _get(self, params: dict[str, str]) -> dict:
        last_error: ClientBridgeError
        for attempt in range(self.retries + 1):
            try:
                response = self.session.get(
                    self.base_url, params=params, timeout=self.timeout
                )
                self._check_response(response)
                return response.json()
            except (NetworkError, RateLimitError, ServerError) as exc:
                last_error = exc
            except ValueError as exc:
                raise APIError("Weather API returned invalid JSON") from exc

            if attempt < self.retries:
                time.sleep(self.backoff_factor * (2**attempt))

        raise last_error

    @staticmethod
    def _check_response(response: requests.Response) -> None:
        if response.ok:
            return

        status_code = response.status_code
        try:
            message = response.json().get("message", response.reason)
        except (ValueError, AttributeError):
            message = response.reason
        message = message or f"Weather API returned status {status_code}"

        if status_code in (401, 403):
            raise AuthenticationError(message, status_code)
        if status_code == 429:
            raise RateLimitError(message, status_code)
        if 500 <= status_code < 600:
            raise ServerError(message, status_code)
        raise APIError(message, status_code)

    @staticmethod
    def _parse(payload: dict, units: str) -> Weather:
        try:
            return Weather(
                city=payload["name"],
                country=payload["sys"]["country"],
                temperature=float(payload["main"]["temp"]),
                feels_like=float(payload["main"]["feels_like"]),
                humidity=int(payload["main"]["humidity"]),
                description=payload["weather"][0]["description"],
                units=units,
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise APIError("Weather API returned an unexpected response") from exc
