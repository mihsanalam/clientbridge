# clientbridge

A small Python client for the OpenWeatherMap current weather API, with a command line interface for quick lookups.

## Requirements

- Python 3.10 or newer
- An OpenWeatherMap API key

## Installation

Install the dependencies from the project directory:

```bash
python -m pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
```

```text
OPENWEATHER_API_KEY=your_api_key_here
```

The key can also be provided directly in the environment. The `.env` file is ignored by Git so credentials stay local.

## Command line usage

```bash
python main.py London
python main.py "New York" --units imperial
```

The command prints the current temperature, feels-like value, condition description, and humidity. `--units` accepts `metric` (the default), `imperial`, and `standard`.

## Library usage

```python
from clientbridge import WeatherClient

client = WeatherClient("your_api_key_here")
weather = client.get_weather("London")
print(weather.temperature, weather.description)
```

`WeatherClient` also accepts `base_url`, `timeout`, `retries`, `backoff_factor`, and `session`. Retries use exponential backoff and apply to network failures, rate limits, and server errors. Authentication errors and other client errors fail immediately.

## Errors

Every failure raised by the package derives from `ClientBridgeError`. `NetworkError` covers connection problems. `APIError` covers unsuccessful or unusable responses and carries a `status_code` attribute; `AuthenticationError`, `RateLimitError`, and `ServerError` are its more specific subclasses. Invalid arguments raise `ValueError`.

## Tests

```bash
python -m unittest discover -s tests
```

The tests use mocked HTTP responses, so they need neither an API key nor a network connection.
