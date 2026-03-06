import os

import requests
from flask import Flask, render_template, request


app = Flask(__name__)


SCALEAPP_BASE_URL = os.getenv(
    "SCALEAPP_BASE_URL",
    "http://nearby-api-env.eba-z23r7ruf.us-east-1.elasticbeanstalk.com",
)


def call_scaleapp_nearby(lat: float, lon: float, place_type: str, radius_m: int) -> dict | None:
    """Call the deployed SCALEAPP /nearby endpoint and return parsed JSON, or None on failure.

    The SCALEAPP API expects radius in meters.
    """
    url = f"{SCALEAPP_BASE_URL}/nearby"
    try:
        response = requests.get(
            url,
            params={"lat": lat, "lon": lon, "type": place_type, "radius": radius_m},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def call_reverse_geocode(lat: float, lon: float) -> dict | None:
    """
    Call a public reverse-geocode API to get human-readable location info for the lat/lon.
    Uses BigDataCloud's free reverse-geocode endpoint (no API key required).
    """
    url = "https://api.bigdatacloud.net/data/reverse-geocode-client"
    try:
        response = requests.get(
            url,
            params={"latitude": lat, "longitude": lon, "localityLanguage": "en"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    error_message: str | None = None
    nearby_data: dict | None = None
    reverse_geo: dict | None = None

    lat_str = ""
    lon_str = ""
    place_type = "cafe"
    radius_str = "1.0"

    if request.method == "POST":
        lat_str = request.form.get("lat", "").strip()
        lon_str = request.form.get("lon", "").strip()
        place_type = request.form.get("type", "cafe").strip() or "cafe"
        radius_str = request.form.get("radius", "1.0").strip() or "1.0"

        if not lat_str or not lon_str:
            error_message = "Latitude and Longitude are required."
        else:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                radius_km = float(radius_str)
                radius_m = int(radius_km * 1000)
            except ValueError:
                error_message = "Latitude and Longitude must be numbers; radius must be a number (km)."
            else:
                nearby_data = call_scaleapp_nearby(lat, lon, place_type, radius_m)
                reverse_geo = call_reverse_geocode(lat, lon)
                if nearby_data is None:
                    error_message = (
                        "Failed to fetch data from the Nearby Places + Weather API. "
                        "Please check that the SCALEAPP service is reachable."
                    )

    return render_template(
        "index.html",
        error_message=error_message,
        nearby_data=nearby_data,
        reverse_geo=reverse_geo,
        lat=lat_str,
        lon=lon_str,
        place_type=place_type,
        radius=radius_str,
        scaleapp_base_url=SCALEAPP_BASE_URL,
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)

