# clientbridge

A small Python wrapper around OpenWeatherMap's current weather and forecast endpoints.

## Set up

Get a free API key from openweathermap.org/api. Copy the example env file and add your key:

```bash
cp .env.example .env
```

```text
OPENWEATHER_API_KEY=your_api_key_here
```

The `.env` file is gitignored, so the key stays on your machine.

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run it

```bash
python main.py London
python main.py "New York" --units imperial --days 2
```

The CLI prints current conditions and a daily forecast. It calls both client methods.

## Use it from Python

```python
from clientbridge import ApiClient

client = ApiClient("your_api_key_here")
weather = client.get_current_weather("London")
forecast = client.get_forecast("London", days=3)
```

Both methods return typed objects, never raw HTTP responses. Failures raise `ApiClientError` with a clear message; timeouts, rate limits, and 5xx replies are retried twice.

## Test it

```bash
python -m unittest discover
```

Tests use mocked responses, so no key or network is needed.
