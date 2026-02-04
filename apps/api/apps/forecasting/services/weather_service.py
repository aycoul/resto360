"""
Weather API Service for BIZ360.

Fetches weather data from OpenWeatherMap API for sales forecasting.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

import requests
from django.conf import settings
from django.utils import timezone

from ..models import WeatherData

logger = logging.getLogger(__name__)


class WeatherServiceError(Exception):
    """Exception for weather service errors."""
    pass


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    # Ivory Coast major cities coordinates
    IVORY_COAST_CITIES = {
        "abidjan": {"lat": 5.3600, "lon": -4.0083},
        "bouake": {"lat": 7.6833, "lon": -5.0333},
        "daloa": {"lat": 6.8833, "lon": -6.4500},
        "yamoussoukro": {"lat": 6.8167, "lon": -5.2833},
        "san-pedro": {"lat": 4.7500, "lon": -6.6333},
        "korhogo": {"lat": 9.4500, "lon": -5.6333},
    }

    def __init__(self, api_key: str = None):
        """
        Initialize weather service.

        Args:
            api_key: OpenWeatherMap API key (uses settings if not provided)
        """
        self.api_key = api_key or getattr(settings, "OPENWEATHERMAP_API_KEY", "")

    def fetch_current_weather(self, lat: float, lon: float) -> dict:
        """
        Fetch current weather for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            dict: Weather data
        """
        if not self.api_key:
            raise WeatherServiceError("OpenWeatherMap API key not configured")

        try:
            response = requests.get(
                f"{self.BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric",
                },
                timeout=10,
            )
            response.raise_for_status()
            return self._parse_current_weather(response.json())
        except requests.RequestException as e:
            logger.error(f"Weather API error: {e}")
            raise WeatherServiceError(f"Failed to fetch weather: {e}")

    def fetch_forecast(self, lat: float, lon: float, days: int = 7) -> List[dict]:
        """
        Fetch weather forecast for a location.

        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days to forecast (max 7 for free tier)

        Returns:
            List[dict]: Daily weather forecasts
        """
        if not self.api_key:
            raise WeatherServiceError("OpenWeatherMap API key not configured")

        try:
            # Use 5-day/3-hour forecast (free tier)
            response = requests.get(
                f"{self.BASE_URL}/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric",
                    "cnt": min(days * 8, 40),  # 8 readings per day
                },
                timeout=10,
            )
            response.raise_for_status()
            return self._parse_forecast(response.json())
        except requests.RequestException as e:
            logger.error(f"Weather forecast API error: {e}")
            raise WeatherServiceError(f"Failed to fetch forecast: {e}")

    def sync_weather_data(self, business) -> int:
        """
        Sync weather data for a business location.

        Args:
            business: Business instance

        Returns:
            int: Number of records synced
        """
        # Get coordinates from business or default to Abidjan
        lat = float(business.latitude) if business.latitude else 5.3600
        lon = float(business.longitude) if business.longitude else -4.0083

        try:
            forecasts = self.fetch_forecast(lat, lon, days=7)
            count = 0

            for forecast in forecasts:
                weather, created = WeatherData.objects.update_or_create(
                    business=business,
                    date=forecast["date"],
                    defaults={
                        "temperature_high": forecast["temp_max"],
                        "temperature_low": forecast["temp_min"],
                        "temperature_avg": forecast.get("temp_avg"),
                        "precipitation_mm": forecast["rain"],
                        "precipitation_probability": forecast.get("pop", 0),
                        "weather_condition": forecast["condition"],
                        "humidity_percent": forecast["humidity"],
                        "wind_speed_kmh": forecast.get("wind_speed", 0),
                        "source": "openweathermap",
                        "fetched_at": timezone.now(),
                    },
                )
                count += 1

            logger.info(f"Synced {count} weather records for {business.name}")
            return count

        except WeatherServiceError as e:
            logger.error(f"Failed to sync weather for {business.name}: {e}")
            return 0

    def _parse_current_weather(self, data: dict) -> dict:
        """Parse current weather API response."""
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})
        rain = data.get("rain", {})

        return {
            "date": date.today(),
            "temp_current": Decimal(str(main.get("temp", 0))),
            "temp_max": Decimal(str(main.get("temp_max", 0))),
            "temp_min": Decimal(str(main.get("temp_min", 0))),
            "humidity": main.get("humidity", 0),
            "condition": self._map_condition(weather.get("main", "")),
            "description": weather.get("description", ""),
            "wind_speed": Decimal(str((wind.get("speed", 0) * 3.6))),  # m/s to km/h
            "rain": Decimal(str(rain.get("1h", 0) or rain.get("3h", 0) or 0)),
        }

    def _parse_forecast(self, data: dict) -> List[dict]:
        """Parse forecast API response into daily summaries."""
        forecasts = data.get("list", [])
        daily = {}

        for item in forecasts:
            dt = datetime.fromtimestamp(item["dt"])
            day = dt.date()

            if day not in daily:
                daily[day] = {
                    "date": day,
                    "temps": [],
                    "humidity": [],
                    "rain": Decimal("0"),
                    "conditions": [],
                    "pop": [],
                    "wind_speeds": [],
                }

            main = item.get("main", {})
            weather = item.get("weather", [{}])[0]
            rain = item.get("rain", {})

            daily[day]["temps"].append(main.get("temp", 0))
            daily[day]["humidity"].append(main.get("humidity", 0))
            daily[day]["rain"] += Decimal(str(rain.get("3h", 0) or 0))
            daily[day]["conditions"].append(weather.get("main", ""))
            daily[day]["pop"].append(item.get("pop", 0) * 100)  # Convert to percentage
            daily[day]["wind_speeds"].append(item.get("wind", {}).get("speed", 0) * 3.6)

        # Aggregate daily data
        result = []
        for day, values in sorted(daily.items()):
            if values["temps"]:
                result.append({
                    "date": day,
                    "temp_max": Decimal(str(max(values["temps"]))),
                    "temp_min": Decimal(str(min(values["temps"]))),
                    "temp_avg": Decimal(str(sum(values["temps"]) / len(values["temps"]))),
                    "humidity": int(sum(values["humidity"]) / len(values["humidity"])),
                    "rain": values["rain"],
                    "condition": self._aggregate_condition(values["conditions"]),
                    "pop": int(max(values["pop"])) if values["pop"] else 0,
                    "wind_speed": Decimal(str(
                        sum(values["wind_speeds"]) / len(values["wind_speeds"])
                    )) if values["wind_speeds"] else Decimal("0"),
                })

        return result

    def _map_condition(self, api_condition: str) -> str:
        """Map OpenWeatherMap condition to our enum."""
        condition_map = {
            "Clear": "sunny",
            "Clouds": "cloudy",
            "Few clouds": "partly_cloudy",
            "Scattered clouds": "partly_cloudy",
            "Broken clouds": "cloudy",
            "Overcast clouds": "cloudy",
            "Rain": "rainy",
            "Drizzle": "rainy",
            "Thunderstorm": "stormy",
            "Snow": "rainy",  # Unlikely in Ivory Coast
            "Mist": "cloudy",
            "Fog": "cloudy",
            "Haze": "harmattan",
            "Dust": "harmattan",
            "Sand": "harmattan",
        }
        return condition_map.get(api_condition, "partly_cloudy")

    def _aggregate_condition(self, conditions: List[str]) -> str:
        """Aggregate multiple conditions into a single dominant condition."""
        if not conditions:
            return "partly_cloudy"

        # Count occurrences
        counts = {}
        for cond in conditions:
            mapped = self._map_condition(cond)
            counts[mapped] = counts.get(mapped, 0) + 1

        # Return most common
        return max(counts, key=counts.get)
