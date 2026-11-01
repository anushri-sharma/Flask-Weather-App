"""Weather app: Flask backend using the free Open-Meteo API (no API key needed)."""
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes -> (description, sky theme used by the front end)
WEATHER_CODES = {
    0: ("Clear sky", "clear"),
    1: ("Mostly clear", "clear"),
    2: ("Partly cloudy", "cloud"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "fog"),
    48: ("Freezing fog", "fog"),
    51: ("Light drizzle", "rain"),
    53: ("Drizzle", "rain"),
    55: ("Heavy drizzle", "rain"),
    56: ("Freezing drizzle", "rain"),
    57: ("Heavy freezing drizzle", "rain"),
    61: ("Light rain", "rain"),
    63: ("Rain", "rain"),
    65: ("Heavy rain", "rain"),
    66: ("Freezing rain", "rain"),
    67: ("Heavy freezing rain", "rain"),
    71: ("Light snow", "snow"),
    73: ("Snow", "snow"),
    75: ("Heavy snow", "snow"),
    77: ("Snow grains", "snow"),
    80: ("Light showers", "rain"),
    81: ("Showers", "rain"),
    82: ("Violent showers", "rain"),
    85: ("Snow showers", "snow"),
    86: ("Heavy snow showers", "snow"),
    95: ("Thunderstorm", "storm"),
    96: ("Thunderstorm with hail", "storm"),
    99: ("Severe thunderstorm with hail", "storm"),
}


def describe(code):
    return WEATHER_CODES.get(code, ("Unknown", "cloud"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/weather")
def weather():
    city = request.args.get("city", "").strip()
    units = request.args.get("units", "metric")
    if not city:
        return jsonify(error="Enter a city name."), 400
    if units not in ("metric", "imperial"):
        units = "metric"

    try:
        geo = requests.get(
            GEOCODE_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=8,
        )
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            return jsonify(error=f"No place found for “{city}”. Check the spelling or add a country."), 404
        place = results[0]

        params = {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                       "weather_code,wind_speed_10m,is_day",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                     "precipitation_probability_max",
            "forecast_days": 6,
            "timezone": "auto",
        }
        if units == "imperial":
            params["temperature_unit"] = "fahrenheit"
            params["wind_speed_unit"] = "mph"

        fc = requests.get(FORECAST_URL, params=params, timeout=8)
        fc.raise_for_status()
        data = fc.json()
    except requests.RequestException:
        return jsonify(error="The weather service didn't respond. Try again in a moment."), 502

    cur = data["current"]
    text, sky = describe(cur["weather_code"])
    daily = data["daily"]

    forecast = []
    for i in range(len(daily["time"])):
        d_text, d_sky = describe(daily["weather_code"][i])
        forecast.append({
            "date": daily["time"][i],
            "summary": d_text,
            "sky": d_sky,
            "high": round(daily["temperature_2m_max"][i]),
            "low": round(daily["temperature_2m_min"][i]),
            "rain_chance": daily["precipitation_probability_max"][i],
        })

    return jsonify({
        "place": {
            "name": place["name"],
            "region": place.get("admin1", ""),
            "country": place.get("country", ""),
        },
        "units": {
            "temp": "°F" if units == "imperial" else "°C",
            "wind": "mph" if units == "imperial" else "km/h",
        },
        "current": {
            "temp": round(cur["temperature_2m"]),
            "feels_like": round(cur["apparent_temperature"]),
            "humidity": cur["relative_humidity_2m"],
            "wind": round(cur["wind_speed_10m"]),
            "summary": text,
            "sky": sky,
            "is_day": bool(cur["is_day"]),
        },
        "forecast": forecast,
    })


if __name__ == "__main__":
    app.run(debug=True)
