import io
import unittest
from contextlib import redirect_stderr
from unittest.mock import Mock, patch

import requests

from clientbridge import ApiClient, ApiClientError
from main import main

CURRENT_WEATHER = {
    "name": "London",
    "sys": {"country": "GB"},
    "main": {"temp": 12.3, "feels_like": 11.1, "humidity": 72},
    "weather": [{"description": "light rain"}],
}

FORECAST = {
    "list": [
        {
            "dt_txt": "2026-11-25 00:00:00",
            "main": {"temp": 10.0, "humidity": 70},
            "weather": [{"description": "clouds"}],
        },
        {
            "dt_txt": "2026-11-25 12:00:00",
            "main": {"temp": 14.0, "humidity": 60},
            "weather": [{"description": "clear sky"}],
        },
        {
            "dt_txt": "2026-11-26 12:00:00",
            "main": {"temp": 15.0, "humidity": 65},
            "weather": [{"description": "sunny"}],
        },
    ]
}


def make_response(status_code=200, payload=None):
    response = Mock()
    response.status_code = status_code
    response.ok = 200 <= status_code < 400
    response.json.return_value = {} if payload is None else payload
    return response


class ApiClientTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.client = ApiClient("test-key", session=self.session)

    def test_get_current_weather_returns_clean_data(self):
        self.session.get.return_value = make_response(payload=CURRENT_WEATHER)

        weather = self.client.get_current_weather("London")

        self.assertEqual(weather.city, "London")
        self.assertEqual(weather.country, "GB")
        self.assertEqual(weather.temperature, 12.3)
        self.assertEqual(weather.feels_like, 11.1)
        self.assertEqual(weather.humidity, 72)
        self.assertEqual(weather.description, "light rain")
        self.assertEqual(weather.units, "metric")

    def test_get_forecast_returns_one_entry_per_day(self):
        self.session.get.return_value = make_response(payload=FORECAST)

        days = self.client.get_forecast("London", days=2)

        self.assertEqual([day.date for day in days], ["2026-11-25", "2026-11-26"])
        self.assertEqual(days[0].temperature, 10.0)
        self.assertEqual(days[0].description, "clouds")

    def test_bad_city_raises_api_client_error(self):
        self.session.get.return_value = make_response(404, {"message": "city not found"})

        with self.assertRaises(ApiClientError) as caught:
            self.client.get_current_weather("Nowhere")

        self.assertIn("city not found", str(caught.exception))
        self.assertEqual(caught.exception.status_code, 404)
        self.session.get.assert_called_once()

    def test_bad_api_key_raises_api_client_error(self):
        self.session.get.return_value = make_response(401, {"message": "Invalid API key"})

        with self.assertRaises(ApiClientError) as caught:
            self.client.get_current_weather("London")

        self.assertIn("Invalid API key", str(caught.exception))

    @patch("clientbridge.client.time.sleep")
    def test_timeout_is_retried_then_raises_api_client_error(self, sleep):
        self.session.get.side_effect = requests.Timeout("timed out")

        with self.assertRaises(ApiClientError) as caught:
            self.client.get_current_weather("London")

        self.assertIn("Could not reach", str(caught.exception))
        self.assertEqual(self.session.get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("clientbridge.client.time.sleep")
    def test_server_error_is_retried(self, sleep):
        self.session.get.side_effect = [
            make_response(500, {"message": "server error"}),
            make_response(payload=CURRENT_WEATHER),
        ]

        weather = self.client.get_current_weather("London")

        self.assertEqual(weather.city, "London")
        self.assertEqual(self.session.get.call_count, 2)
        sleep.assert_called_once()

    def test_invalid_json_raises_api_client_error(self):
        response = make_response()
        response.json.side_effect = ValueError("bad json")
        self.session.get.return_value = response

        with self.assertRaises(ApiClientError):
            self.client.get_current_weather("London")

    def test_invalid_units_raises_api_client_error(self):
        with self.assertRaises(ApiClientError):
            self.client.get_current_weather("London", units="kelvin")
        self.session.get.assert_not_called()

    def test_empty_api_key_is_rejected(self):
        with self.assertRaises(ApiClientError):
            ApiClient("")


class CliTests(unittest.TestCase):
    @patch.dict("os.environ", {"OPENWEATHER_API_KEY": "test-key"})
    @patch("main.ApiClient")
    def test_failure_prints_message_without_traceback(self, client_class):
        client_class.return_value.get_current_weather.side_effect = ApiClientError(
            "city not found"
        )

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main(["Nowhere"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Error: city not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
