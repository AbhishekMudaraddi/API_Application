import os
import math
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS


app = Flask(__name__)

# CORS: browsers block cross-origin fetch unless the API sends Access-Control-Allow-Origin.
# Without this, pages on http://127.0.0.1:5500 (Live Server) cannot call https://api.abhishekmudaraddi.com.
# Optional: set CORS_ORIGINS="https://mysite.com,http://127.0.0.1:5500" to allow only listed origins.
_cors_origins = os.getenv("CORS_ORIGINS", "").strip()
if _cors_origins:
    CORS(app, origins=[o.strip() for o in _cors_origins.split(",") if o.strip()])
else:
    CORS(app)  # allow any origin (public GET API)

# Read API keys from environment variables.
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two lat/lon points using the haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def map_place_type_to_google(place_type: str) -> str:
    """
    Map a simple place type (cafe, restaurant, xerox, etc.) to a Google Places type/keyword.
    Extend this mapping as needed for your project.
    """
    mapping = {
        "cafe": "cafe",
        "restaurant": "restaurant",
        "xerox": "print_shop",
        "copyshop": "print_shop",
        "atm": "atm",
        "pharmacy": "pharmacy",
        "library": "library",
    }
    return mapping.get(place_type.lower(), place_type.lower())


def fetch_places(lat: float, lon: float, place_type: str, radius: int) -> list[dict]:
    """
    Query Google Places for nearby places of a given type around (lat, lon).
    Returns at most 5 places sorted by distance from the given point.
    """
    if not GOOGLE_PLACES_API_KEY:
        # If no key is configured, behave gracefully and return no places.
        return []

    g_type_or_keyword = map_place_type_to_google(place_type)
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": radius,
        "keyword": g_type_or_keyword,
        "key": GOOGLE_PLACES_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
    except (requests.exceptions.Timeout, requests.exceptions.HTTPError):
        # Upstream Google Places call failed; return no places.
        return []

    data = response.json()

    status = data.get("status")
    if status not in ("OK", "ZERO_RESULTS"):
        # API-level error (e.g., OVER_QUERY_LIMIT, REQUEST_DENIED, etc.)
        return []

    results: list[dict] = []
    for result in data.get("results", []):
        geometry = result.get("geometry", {})
        location = geometry.get("location", {})
        el_lat = location.get("lat")
        el_lon = location.get("lng")
        if el_lat is None or el_lon is None:
            continue

        name = result.get("name", "Unknown")
        vicinity = result.get("vicinity") or result.get("formatted_address") or ""

        distance = haversine_distance_m(lat, lon, el_lat, el_lon)

        results.append(
            {
                "name": name,
                "lat": el_lat,
                "lon": el_lon,
                "distanceMeters": round(distance, 1),
                "address": vicinity,
                "source": "GooglePlaces",
            }
        )

    # sort by distance and keep top 5
    results.sort(key=lambda x: x["distanceMeters"])
    return results[:5]


def fetch_weather(lat: float, lon: float) -> dict | None:
    """
    Fetch current weather for (lat, lon) from OpenWeatherMap.
    Returns a small dict or None if the API key is not set or the call fails.
    """
    if not OPENWEATHER_API_KEY:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    main = data.get("main", {})
    temp = main.get("temp")

    desc = ""
    if data.get("weather"):
        desc = data["weather"][0].get("description", "")

    return {
        "temperature": temp,
        "description": desc,
    }


@app.route("/", methods=["GET"])
def root() -> tuple[dict, int]:
    """
    Simple health-check / info endpoint for Elastic Beanstalk and humans.
    """
    return (
        jsonify(
            {
                "status": "ok",
                "message": "Nearby Places + Weather API",
                "endpoints": ["/nearby"],
            }
        ),
        200,
    )


@app.route("/nearby", methods=["GET"])
def nearby() -> tuple[dict, int] | tuple[dict, int, dict]:
    """
    Public API endpoint.

    Query parameters:
      - lat (required): latitude
      - lon (required): longitude
      - type (optional, default "cafe"): place type (cafe, restaurant, xerox, etc.)
      - radius (optional, default 1000): search radius in meters
    """
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    place_type = request.args.get("type", "cafe")
    radius = request.args.get("radius", "1000")

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required query parameters"}), 400

    try:
        lat_f = float(lat)
        lon_f = float(lon)
        radius_i = int(radius)
    except ValueError:
        return (
            jsonify(
                {
                    "error": "lat and lon must be numbers; radius must be an integer (meters)",
                }
            ),
            400,
        )

    # Fetch nearby places
    try:
        places = fetch_places(lat_f, lon_f, place_type, radius_i)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Failed to fetch places from provider: {exc}"}), 502

    # Fetch weather (non-fatal if it fails)
    weather: dict | None
    try:
        weather = fetch_weather(lat_f, lon_f)
    except Exception:
        weather = None

    response = {
        "location": {"lat": lat_f, "lon": lon_f},
        "placeType": place_type,
        "radiusMeters": radius_i,
        "weather": weather,
        "places": places,
    }
    return jsonify(response), 200


if __name__ == "__main__":
    # Local development entry point: python app.py
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

