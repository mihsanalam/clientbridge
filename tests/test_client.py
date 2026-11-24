import unittest
from unittest.mock import Mock, patch

import requests

from clientbridge.client import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, WeatherClient
from clientbridge.exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
    ServerError,
)

SAMPLE_WEATHER = {
    "weather": [{"description": "light rain"}],
    "main": {"temp": 12.3, "feels_like": 11.1, "humidity": 72},
    "name": "London",
    "sys": {"country": "GB"},
}


def make_response(status_code=200, payload=None, reason=""):
    response = Mock()
    response.status_code = status_code
    response.ok = 200 <= status_code < 400
    response.reason = reason
    response.json.return_value = {} if payload is None else payload
    return response


class WeatherClientTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.client = WeatherClient("test-key", session=self.session)

    def test_get_weather_parses_response(self):
        self.session.get.return_value = make_response(payload=SAMPLE_WEATHER)

        weather = self.client.get_weather("London")

        self.assertEqual(weather.city, "London")
        self.assertEqual(weather.country, "GB")
        self.assertEqual(weather.temperature, 12.3)
        self.assertEqual(weather.feels_like, 11.1)
        self.assertEqual(weather.humidity, 72)
        self.assertEqual(weather.description, "light rain")
        self.assertEqual(weather.units, "metric")
        self.session.get.assert_called_once_with(
            DEFAULT_BASE_URL,
            params={"q": "London", "appid": "test-key", "units": "metric"},
            timeout=DEFAULT_TIMEOUT,
        )

    def test_get_weather_passes_units(self):
        self.session.get.return_value = make_response(payload=SAMPLE_WEATHER)

        weather = self.client.get_weather("London", units="imperial")

        self.assertEqual(weather.units, "imperial")
        self.assertEqual(
            self.session.get.call_args.kwargs["params"]["units"], "imperial"
        )

    def test_rejects_invalid_units(self):
        with self.assertRaises(ValueError):
            self.client.get_weather("London", units="kelvin")
        self.session.get.assert_not_called()

    def test_rejects_empty_city(self):
        with self.assertRaises(ValueError):
            self.client.get_weather("   ")
        self.session.get.assert_not_called()

    def test_requires_api_key(self):
        with self.assertRaises(ValueError):
            WeatherClient("")

    @patch("clientbridge.client.time.sleep")
    def test_rate_limit_is_retried(self, sleep):
        self.session.get.side_effect = [
            make_response(429, {"message": "rate limited"}),
            make_response(payload=SAMPLE_WEATHER),
        ]

        weather = self.client.get_weather("London")

        self.assertEqual(weather.city, "London")
        self.assertEqual(self.session.get.call_count, 2)
        sleep.assert_called_once()

    def test_authentication_error_is_not_retried(self):
        self.session.get.return_value = make_response(401, {"message": "Invalid key"})

        with self.assertRaises(AuthenticationError):
            self.client.get_weather("London")

        self.session.get.assert_called_once()

    def test_client_error_is_not_retried(self):
        self.session.get.return_value = make_response(404, {"message": "not found"})

        with self.assertRaises(APIError):
            self.client.get_weather("Nowhere")

        self.session.get.assert_called_once()

    @patch("clientbridge.client.time.sleep")
    def test_network_error_is_retried_then_raised(self, sleep):
        self.session.get.side_effect = requests.ConnectionError("offline")

        with self.assertRaises(NetworkError):
            self.client.get_weather("London")

        self.assertEqual(self.session.get.call_count, self.client.retries + 1)
        self.assertEqual(sleep.call_count, self.client.retries)

    @patch("clientbridge.client.time.sleep")
    def test_server_error_exhausts_retries(self, sleep):
        self.session.get.return_value = make_response(500, {"message": "boom"})

        with self.assertRaises(ServerError) as caught:
            self.client.get_weather("London")

        self.assertEqual(caught.exception.status_code, 500)
        self.assertEqual(self.session.get.call_count, self.client.retries + 1)
        self.assertEqual(sleep.call_count, self.client.retries)

    def test_zero_retries(self):
        client = WeatherClient("test-key", retries=0, session=self.session)
        self.session.get.side_effect = requests.ConnectionError("offline")

        with self.assertRaises(NetworkError):
            client.get_weather("London")

        self.session.get.assert_called_once()

    def test_invalid_json_raises_api_error(self):
        response = make_response()
        response.json.side_effect = ValueError("bad json")
        self.session.get.return_value = response

        with self.assertRaises(APIError):
            self.client.get_weather("London")

        self.session.get.assert_called_once()

    def test_unexpected_payload_raises_api_error(self):
        self.session.get.return_value = make_response(payload={"unexpected": True})

        with self.assertRaises(APIError):
            self.client.get_weather("London")


if __name__ == "__main__":
    unittest.main()
