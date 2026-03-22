import os

import requests
from flask import Flask, Response, render_template, request

app = Flask(__name__)

# Max upload size for compress proxy (API Gateway often limits ~10MB; adjust as needed)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

SCALEAPP_BASE_URL = os.getenv(
    "SCALEAPP_BASE_URL",
    "https://api.abhishekmudaraddi.com",
)

COMPRESS_API_URL = os.getenv(
    "COMPRESS_API_URL",
    "https://4ecpi9z5mj.execute-api.us-east-1.amazonaws.com/compress",
)
# Multipart field name expected by the upstream API (ask your friend if uploads fail)
COMPRESS_FILE_FIELD = os.getenv("COMPRESS_FILE_FIELD", "file")


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


@app.route("/compress", methods=["POST"])
def compress_proxy():
    """Forward uploaded file to the classmate's compress API and return the compressed file."""
    f = request.files.get(COMPRESS_FILE_FIELD)
    if not f or not f.filename:
        return {"error": "No file uploaded"}, 400

    headers = {}
    api_key = os.getenv("COMPRESS_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    # Stream upload to upstream (field name must match their API)
    files = {
        COMPRESS_FILE_FIELD: (
            f.filename,
            f.stream,
            f.mimetype or "application/octet-stream",
        ),
    }
    try:
        upstream = requests.post(
            COMPRESS_API_URL,
            files=files,
            headers=headers,
            timeout=300,
        )
    except requests.RequestException as exc:
        return {"error": f"Upstream request failed: {exc!s}"}, 502

    if upstream.status_code >= 400:
        try:
            err = upstream.json()
        except Exception:
            err = {"error": upstream.text[:2000] if upstream.text else "Upstream error"}
        return err, upstream.status_code

    content_type = upstream.headers.get(
        "Content-Type",
        "application/octet-stream",
    )
    out = Response(upstream.content, mimetype=content_type)
    cd = upstream.headers.get("Content-Disposition")
    if cd:
        out.headers["Content-Disposition"] = cd
    else:
        base = f.filename.rsplit(".", 1)[0] if "." in f.filename else f.filename
        ext = f.filename.rsplit(".", 1)[-1] if "." in f.filename else "bin"
        out.headers["Content-Disposition"] = (
            f'attachment; filename="compressed_{base}.{ext}"'
        )
    return out


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

