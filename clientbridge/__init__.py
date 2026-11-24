"""Fetch current weather data from OpenWeatherMap."""

from .client import Weather, WeatherClient
from .exceptions import (
    APIError,
    AuthenticationError,
    ClientBridgeError,
    NetworkError,
    RateLimitError,
    ServerError,
)

__all__ = [
    "APIError",
    "AuthenticationError",
    "ClientBridgeError",
    "NetworkError",
    "RateLimitError",
    "ServerError",
    "Weather",
    "WeatherClient",
]

__version__ = "0.1.0"
