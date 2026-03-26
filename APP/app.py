import os
import math
from urllib.parse import quote

import requests
from flask import Flask, Response, jsonify, render_template, request

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
IMAGE_API_BASE_URL = os.getenv(
    "IMAGE_API_BASE_URL",
    "https://n3vdm98ezc.execute-api.us-east-1.amazonaws.com",
)
IMAGE_PUBLIC_BASE_URL = os.getenv(
    "IMAGE_PUBLIC_BASE_URL",
    "http://image-core-cloud.s3-website-us-east-1.amazonaws.com",
)
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


def _extract_image_uri(payload: dict) -> str | None:
    """Extract a likely image object key from upstream payload."""
    if not isinstance(payload, dict):
        return None
    candidates = (
        payload.get("uri"),
        payload.get("key"),
        payload.get("path"),
        payload.get("s3Key"),
        payload.get("objectKey"),
        payload.get("imageKey"),
        payload.get("outputKey"),
    )
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return None


def _build_public_image_url(uri: str | None) -> str | None:
    if not uri:
        return None
    if uri.startswith("http://") or uri.startswith("https://"):
        return uri
    base = IMAGE_PUBLIC_BASE_URL.rstrip("/")
    cleaned = uri.lstrip("/")
    # Keep / separators while escaping special chars in each segment.
    encoded = "/".join(quote(seg) for seg in cleaned.split("/"))
    return f"{base}/{encoded}"


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


def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _planner_get_places_with_images(lat: float, lon: float, place_type: str, limit: int = 5) -> list[dict]:
    """Planner-specific place search using Google Places directly with photo URLs."""
    if not GOOGLE_PLACES_API_KEY:
        return []

    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
        params={
            "location": f"{lat},{lon}",
            "radius": 2000,
            "keyword": place_type,
            "key": GOOGLE_PLACES_API_KEY,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    status = payload.get("status")
    if status not in ("OK", "ZERO_RESULTS"):
        return []

    places: list[dict] = []
    for result in payload.get("results", []):
        loc = (result.get("geometry") or {}).get("location") or {}
        p_lat = loc.get("lat")
        p_lon = loc.get("lng")
        if p_lat is None or p_lon is None:
            continue

        photos = result.get("photos") or []
        photo_ref = None
        if photos and isinstance(photos[0], dict):
            photo_ref = photos[0].get("photo_reference")

        image_url = None
        if photo_ref:
            image_url = (
                "https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=700&photo_reference={quote(str(photo_ref))}&key={quote(GOOGLE_PLACES_API_KEY)}"
            )

        places.append(
            {
                "name": result.get("name", "Unknown"),
                "rating": result.get("rating", "N/A"),
                "address": result.get("vicinity") or result.get("formatted_address") or "N/A",
                "lat": p_lat,
                "lon": p_lon,
                "distanceMeters": round(_haversine_distance_m(lat, lon, p_lat, p_lon), 1),
                "imageUrl": image_url,
                "photoReference": photo_ref,
                "source": "GooglePlacesDirect",
            }
        )

    places.sort(key=lambda x: x["distanceMeters"])
    return places[:limit]


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


@app.route("/image/upload", methods=["POST"])
def image_upload_proxy():
    """Upload image file to classmate image API and return parsed metadata."""
    f = request.files.get("file")
    if not f or not f.filename:
        return {"error": "No image file uploaded"}, 400

    files = {"file": (f.filename, f.stream, f.mimetype or "application/octet-stream")}
    try:
        upstream = requests.post(
            f"{IMAGE_API_BASE_URL.rstrip('/')}/upload",
            files=files,
            timeout=180,
        )
    except requests.RequestException as exc:
        return {"error": f"Image upload upstream failed: {exc!s}"}, 502

    try:
        payload = upstream.json()
    except Exception:
        payload = {"raw": upstream.text[:2000] if upstream.text else ""}

    if upstream.status_code >= 400:
        return payload, upstream.status_code

    uri = _extract_image_uri(payload)
    url = payload.get("url") if isinstance(payload, dict) else None
    if not isinstance(url, str) or not url.strip():
        url = _build_public_image_url(uri)

    return jsonify(
        {
            "ok": True,
            "uri": uri,
            "url": url,
            "upstream": payload,
        }
    )


@app.route("/image/transform", methods=["POST"])
def image_transform_proxy():
    """Call classmate transform API and return transformed image metadata."""
    body = request.get_json(silent=True) or {}
    uri = str(body.get("uri", "")).strip()
    action = str(body.get("action", "")).strip()
    parameters = body.get("parameters")

    if not uri:
        return {"error": "uri is required"}, 400
    if not action:
        return {"error": "action is required"}, 400

    upstream_payload: dict = {"uri": uri, "action": action}
    if isinstance(parameters, dict) and parameters:
        upstream_payload["parameters"] = parameters

    try:
        upstream = requests.post(
            f"{IMAGE_API_BASE_URL.rstrip('/')}/transform",
            json=upstream_payload,
            timeout=240,
        )
    except requests.RequestException as exc:
        return {"error": f"Image transform upstream failed: {exc!s}"}, 502

    try:
        payload = upstream.json()
    except Exception:
        payload = {"raw": upstream.text[:2000] if upstream.text else ""}

    if upstream.status_code >= 400:
        return payload, upstream.status_code

    transformed_uri = _extract_image_uri(payload) or uri
    transformed_url = payload.get("url") if isinstance(payload, dict) else None
    if not isinstance(transformed_url, str) or not transformed_url.strip():
        transformed_url = _build_public_image_url(transformed_uri)

    return jsonify(
        {
            "ok": True,
            "uri": transformed_uri,
            "url": transformed_url,
            "upstream": payload,
        }
    )


@app.route("/planner/nearby", methods=["POST"])
def planner_nearby():
    """Planner endpoint: use current location + place keyword and return top nearby places."""
    body = request.get_json(silent=True) or {}
    lat = body.get("lat")
    lon = body.get("lon")
    place_type = str(body.get("type", "cafe")).strip() or "cafe"

    if lat is None or lon is None:
        return {"error": "lat and lon are required"}, 400

    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except ValueError:
        return {"error": "lat and lon must be numbers"}, 400

    places = _planner_get_places_with_images(lat_f, lon_f, place_type, 5)
    if GOOGLE_PLACES_API_KEY and not places:
        return {"error": "No nearby places found or Google Places returned no results."}, 404
    if not GOOGLE_PLACES_API_KEY:
        return {"error": "Planner image search requires GOOGLE_PLACES_API_KEY in APP environment."}, 500

    nearby_data = {"places": places}
    reverse_geo = call_reverse_geocode(lat_f, lon_f)

    return jsonify(
        {
            "ok": True,
            "input": {"lat": lat_f, "lon": lon_f, "type": place_type},
            "nearby": nearby_data,
            "reverseGeo": reverse_geo,
        }
    )


@app.route("/planner/annotate-image", methods=["POST"])
def planner_annotate_image():
    """Blur planner image slightly, then overlay centered rating + distance text."""
    body = request.get_json(silent=True) or {}
    image_url = str(body.get("imageUrl", "")).strip()
    rating = body.get("rating", "N/A")
    distance = body.get("distanceMeters", "N/A")

    if not image_url:
        return {"error": "imageUrl is required"}, 400

    try:
        image_resp = requests.get(image_url, timeout=45)
        image_resp.raise_for_status()
    except requests.RequestException as exc:
        return {"error": f"Failed to download source image: {exc!s}"}, 502

    upload_files = {
        "file": (
            "planner-image.jpg",
            image_resp.content,
            image_resp.headers.get("Content-Type", "image/jpeg"),
        )
    }
    try:
        upload_resp = requests.post(
            f"{IMAGE_API_BASE_URL.rstrip('/')}/upload",
            files=upload_files,
            timeout=180,
        )
    except requests.RequestException as exc:
        return {"error": f"Image upload upstream failed: {exc!s}"}, 502

    try:
        upload_payload = upload_resp.json()
    except Exception:
        upload_payload = {"raw": upload_resp.text[:2000] if upload_resp.text else ""}

    if upload_resp.status_code >= 400:
        return upload_payload, upload_resp.status_code

    uri = _extract_image_uri(upload_payload)
    if not uri:
        return {"error": "Upload succeeded but no image uri was returned."}, 502

    # 1) Normalize image dimensions so text coordinates map consistently.
    resize_payload = {
        "uri": uri,
        "action": "resize",
        "parameters": {
            "width": 700,
            "height": 400,
        },
    }
    try:
        resize_resp = requests.post(
            f"{IMAGE_API_BASE_URL.rstrip('/')}/transform",
            json=resize_payload,
            timeout=240,
        )
    except requests.RequestException as exc:
        return {"error": f"Image resize upstream failed: {exc!s}"}, 502

    try:
        resize_result_payload = resize_resp.json()
    except Exception:
        resize_result_payload = {"raw": resize_resp.text[:2000] if resize_resp.text else ""}

    if resize_resp.status_code >= 400:
        return resize_result_payload, resize_resp.status_code

    resized_uri = _extract_image_uri(resize_result_payload) or uri

    # 2) Convert to grayscale for better readability.
    grayscale_payload = {
        "uri": resized_uri,
        "action": "grayscale",
    }
    try:
        grayscale_resp = requests.post(
            f"{IMAGE_API_BASE_URL.rstrip('/')}/transform",
            json=grayscale_payload,
            timeout=240,
        )
    except requests.RequestException as exc:
        return {"error": f"Image grayscale upstream failed: {exc!s}"}, 502

    try:
        grayscale_result_payload = grayscale_resp.json()
    except Exception:
        grayscale_result_payload = {"raw": grayscale_resp.text[:2000] if grayscale_resp.text else ""}

    if grayscale_resp.status_code >= 400:
        return grayscale_result_payload, grayscale_resp.status_code

    grayscale_uri = _extract_image_uri(grayscale_result_payload) or resized_uri

    # 3) Light blur for better text readability.
    blur_payload = {
        "uri": grayscale_uri,
        "action": "blur",
        "parameters": {
            "blur_radius": 1,
        },
    }
    try:
        blur_resp = requests.post(
            f"{IMAGE_API_BASE_URL.rstrip('/')}/transform",
            json=blur_payload,
            timeout=240,
        )
    except requests.RequestException as exc:
        return {"error": f"Image blur upstream failed: {exc!s}"}, 502

    try:
        blur_result_payload = blur_resp.json()
    except Exception:
        blur_result_payload = {"raw": blur_resp.text[:2000] if blur_resp.text else ""}

    if blur_resp.status_code >= 400:
        return blur_result_payload, blur_resp.status_code

    blurred_uri = _extract_image_uri(blur_result_payload) or grayscale_uri

    # 4) Add centered text.
    label_text = f"Rating: {rating}  |  Distance: {distance} m"
    approx_text_x = max(20, int((700 / 2) - (len(label_text) * 8.2)))
    text_payload = {
        "uri": blurred_uri,
        "action": "text",
        "parameters": {
            "text": label_text,
            "font_size": 32,
            "font_color": "(255,255,255,255)",
            "angle": 0,
            "text_x": approx_text_x,
            "text_y": 200,
        },
    }
    try:
        text_resp = requests.post(
            f"{IMAGE_API_BASE_URL.rstrip('/')}/transform",
            json=text_payload,
            timeout=240,
        )
    except requests.RequestException as exc:
        return {"error": f"Image text transform upstream failed: {exc!s}"}, 502

    try:
        transformed_payload = text_resp.json()
    except Exception:
        transformed_payload = {"raw": text_resp.text[:2000] if text_resp.text else ""}

    if text_resp.status_code >= 400:
        return transformed_payload, text_resp.status_code

    transformed_uri = _extract_image_uri(transformed_payload) or blurred_uri
    transformed_url = transformed_payload.get("url") if isinstance(transformed_payload, dict) else None
    if not isinstance(transformed_url, str) or not transformed_url.strip():
        transformed_url = _build_public_image_url(transformed_uri)

    return jsonify(
        {
            "ok": True,
            "uri": transformed_uri,
            "url": transformed_url,
            "upstream": transformed_payload,
        }
    )


@app.route("/planner/process-image", methods=["POST"])
def planner_process_image():
    """Planner helper: download an image URL, upload, then apply selected transform."""
    body = request.get_json(silent=True) or {}
    image_url = str(body.get("imageUrl", "")).strip()
    action = str(body.get("action", "")).strip()
    parameters = body.get("parameters")

    if not image_url:
        return {"error": "imageUrl is required"}, 400
    if not action:
        return {"error": "action is required"}, 400

    try:
        image_resp = requests.get(image_url, timeout=45)
        image_resp.raise_for_status()
    except requests.RequestException as exc:
        return {"error": f"Failed to download source image: {exc!s}"}, 502

    upload_files = {
        "file": (
            "planner-image.jpg",
            image_resp.content,
            image_resp.headers.get("Content-Type", "image/jpeg"),
        )
    }
    try:
        upload_resp = requests.post(
            f"{IMAGE_API_BASE_URL.rstrip('/')}/upload",
            files=upload_files,
            timeout=180,
        )
    except requests.RequestException as exc:
        return {"error": f"Image upload upstream failed: {exc!s}"}, 502

    try:
        upload_payload = upload_resp.json()
    except Exception:
        upload_payload = {"raw": upload_resp.text[:2000] if upload_resp.text else ""}

    if upload_resp.status_code >= 400:
        return upload_payload, upload_resp.status_code

    uri = _extract_image_uri(upload_payload)
    if not uri:
        return {"error": "Upload succeeded but no image uri was returned."}, 502

    transform_payload: dict = {"uri": uri, "action": action}
    if isinstance(parameters, dict) and parameters:
        transform_payload["parameters"] = parameters

    try:
        transform_resp = requests.post(
            f"{IMAGE_API_BASE_URL.rstrip('/')}/transform",
            json=transform_payload,
            timeout=240,
        )
    except requests.RequestException as exc:
        return {"error": f"Image transform upstream failed: {exc!s}"}, 502

    try:
        transformed_payload = transform_resp.json()
    except Exception:
        transformed_payload = {"raw": transform_resp.text[:2000] if transform_resp.text else ""}

    if transform_resp.status_code >= 400:
        return transformed_payload, transform_resp.status_code

    transformed_uri = _extract_image_uri(transformed_payload) or uri
    transformed_url = transformed_payload.get("url") if isinstance(transformed_payload, dict) else None
    if not isinstance(transformed_url, str) or not transformed_url.strip():
        transformed_url = _build_public_image_url(transformed_uri)

    return jsonify(
        {
            "ok": True,
            "uri": transformed_uri,
            "url": transformed_url,
            "upstream": transformed_payload,
        }
    )


@app.route("/", methods=["GET", "POST"])
def index():
    error_message: str | None = None
    nearby_data: dict | None = None
    reverse_geo: dict | None = None
    active_tab = request.args.get("tab", "planner")

    lat_str = ""
    lon_str = ""
    place_type = "cafe"
    radius_str = "1.0"

    if request.method == "POST":
        active_tab = "playground"
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
        active_tab=active_tab,
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)

