# clientbridge

A small Python wrapper around the OpenWeatherMap REST API, built as a homework exercise in making a third-party API usable and reliable.

## Getting a key

Create a free account at openweathermap.org/api and generate an API key. Copy `.env.example` to `.env` and put the key there:

```bash
cp .env.example .env
```

```text
OPENWEATHER_API_KEY=your_api_key_here
```

`.env` is gitignored, so the key is never committed.

## Install

```bash
python -m pip install -r requirements.txt
```

## Run the CLI

```bash
python main.py London
python main.py "New York" --units imperial --days 2
```

The CLI prints current conditions followed by a daily forecast. It calls both client methods end to end.

## Use the client directly

```python
from clientbridge import ApiClient

client = ApiClient("your_api_key_here")
weather = client.get_current_weather("London")
forecast = client.get_forecast("London", days=3)
```

Both methods return small typed objects rather than raw HTTP responses. Network errors, HTTP errors, and invalid JSON raise `ApiClientError` with a readable message. Timeouts, rate limits, and 5xx responses are retried twice with a short delay.

## Tests

```bash
python -m unittest discover
```

The tests use mocked HTTP responses, so no key or network connection is needed. They include failure cases for a bad city, a bad key, and a timeout.
