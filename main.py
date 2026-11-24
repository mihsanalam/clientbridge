"""Command line interface for fetching current weather."""

import argparse
import os
import sys

from dotenv import load_dotenv

from clientbridge.client import WeatherClient
from clientbridge.exceptions import ClientBridgeError

UNIT_SYMBOLS = {"metric": "C", "imperial": "F", "standard": "K"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print the current weather for a city."
    )
    parser.add_argument("city", help="city name, optionally followed by a country code")
    parser.add_argument(
        "-u",
        "--units",
        choices=tuple(UNIT_SYMBOLS),
        default="metric",
        help="temperature units (default: metric)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        print(
            "Error: set OPENWEATHER_API_KEY in the environment or a .env file.",
            file=sys.stderr,
        )
        return 1

    args = build_parser().parse_args(argv)
    client = WeatherClient(api_key)
    try:
        weather = client.get_weather(args.city, units=args.units)
    except ClientBridgeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    symbol = UNIT_SYMBOLS[weather.units]
    print(
        f"{weather.city}, {weather.country}: {weather.temperature:.1f}°{symbol}, "
        f"feels like {weather.feels_like:.1f}°{symbol}. "
        f"{weather.description.capitalize()}. Humidity {weather.humidity}%."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
