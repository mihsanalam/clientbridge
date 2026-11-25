"""Small wrapper around the OpenWeatherMap REST API."""

import time
from dataclasses import dataclass
from typing import Optional

import requests

from .exceptions import ApiClientError

BASE_URL = "https://api.openweathermap.org/data/2.5"
TIMEOUT = 10
RETRIES = 2
RETRY_DELAY = 1
VALID_UNITS = ("metric", "imperial", "standard")


@dataclass(frozen=True)
class Weather:
    """Current conditions at a location."""

    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    description: str
    units: str


@dataclass(frozen=True)
class ForecastDay:
    """One daily forecast entry."""

    date: str
    temperature: float
    description: str
    humidity: int


class ApiClient:
    """Fetch current weather and a short forecast from OpenWeatherMap."""

    def __init__(self, api_key: str, session: Optional[requests.Session] = None) -> None:
        if not api_key:
            raise ApiClientError("An API key is required")
        self.api_key = api_key
        self.session = session if session is not None else requests.Session()

    def get_current_weather(self, city: str, units: str = "metric") -> Weather:
        """Return the current conditions for ``city``."""
        payload = self._request("weather", city, units)
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
            raise ApiClientError("Current weather response had an unexpected format") from exc

    def get_forecast(
        self, city: str, days: int = 3, units: str = "metric"
    ) -> list[ForecastDay]:
        """Return one forecast entry per day, up to ``days`` days."""
        if days < 1:
            raise ApiClientError("days must be at least 1")

        payload = self._request("forecast", city, units)
        forecasts: list[ForecastDay] = []
        seen_dates: set[str] = set()
        try:
            for item in payload["list"]:
                date = item["dt_txt"].split(" ")[0]
                if date in seen_dates:
                    continue
                seen_dates.add(date)
                forecasts.append(
                    ForecastDay(
                        date=date,
                        temperature=float(item["main"]["temp"]),
                        description=item["weather"][0]["description"],
                        humidity=int(item["main"]["humidity"]),
                    )
                )
                if len(forecasts) == days:
                    break
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ApiClientError("Forecast response had an unexpected format") from exc

        return forecasts

    def _request(self, endpoint: str, city: str, units: str) -> dict:
        if not city.strip():
            raise ApiClientError("A city name is required")
        if units not in VALID_UNITS:
            raise ApiClientError(f"units must be one of: {', '.join(VALID_UNITS)}")

        url = f"{BASE_URL}/{endpoint}"
        params = {"q": city, "appid": self.api_key, "units": units}
        last_error: ApiClientError

        for attempt in range(RETRIES + 1):
            try:
                response = self.session.get(url, params=params, timeout=TIMEOUT)
            except requests.RequestException as exc:
                last_error = ApiClientError(f"Could not reach the weather API: {exc}")
            else:
                if response.ok:
                    try:
                        return response.json()
                    except ValueError as exc:
                        raise ApiClientError("Weather API returned invalid JSON") from exc

                error = ApiClientError(self._error_message(response), response.status_code)
                if response.status_code == 429 or response.status_code >= 500:
                    last_error = error
                else:
                    raise error

            if attempt < RETRIES:
                time.sleep(RETRY_DELAY)

        raise last_error

    @staticmethod
    def _error_message(response: requests.Response) -> str:
        try:
            message = response.json().get("message")
        except (ValueError, AttributeError):
            message = None
        return message or f"Weather API returned HTTP {response.status_code}"
