"""Command line interface for the OpenWeatherMap wrapper."""

import argparse
import os
import sys

from dotenv import load_dotenv

from clientbridge import ApiClient, ApiClientError

UNIT_SYMBOLS = {"metric": "C", "imperial": "F", "standard": "K"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show current weather and a short forecast.")
    parser.add_argument("city", help="city name")
    parser.add_argument(
        "-u",
        "--units",
        choices=tuple(UNIT_SYMBOLS),
        default="metric",
        help="temperature units (default: metric)",
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=3,
        help="number of forecast days (default: 3)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv()
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        print("Error: set OPENWEATHER_API_KEY in .env or the environment.", file=sys.stderr)
        return 1

    client = ApiClient(api_key)
    try:
        weather = client.get_current_weather(args.city, units=args.units)
        forecast = client.get_forecast(args.city, days=args.days, units=args.units)
    except ApiClientError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    symbol = UNIT_SYMBOLS[weather.units]
    print(
        f"{weather.city}, {weather.country}: {weather.temperature:.1f}°{symbol}, "
        f"feels like {weather.feels_like:.1f}°{symbol}. "
        f"{weather.description.capitalize()}. Humidity {weather.humidity}%."
    )
    print("Forecast:")
    for day in forecast:
        print(f"  {day.date}: {day.temperature:.1f}°{symbol}, {day.description}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
