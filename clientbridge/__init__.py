"""Wrapper around the OpenWeatherMap REST API."""

from .client import ApiClient, ForecastDay, Weather
from .exceptions import ApiClientError
