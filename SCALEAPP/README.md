# Nearby Places + Weather API

A public REST API that returns **nearby places** (cafes, restaurants, ATMs, etc.) and **current weather** for any latitude/longitude. Built with **Flask**, powered by **Google Places** and **OpenWeatherMap**. Deployed on **AWS Elastic Beanstalk**.

---

## Base URL

**Live API:**

```
https://api.abhishekmudaraddi.com
```

Use this as the base for all requests below. For local development, use `http://localhost:5000` instead.

---

## Endpoints

### 1. Health check (root)

Simple check that the API is up.

| Item        | Value        |
|------------|--------------|
| **Method** | `GET`        |
| **Path**   | `/`          |
| **Params** | None         |

**Example request**

```bash
curl "https://api.abhishekmudaraddi.com/"
```

**Example response** (`200 OK`)

```json
{
  "status": "ok",
  "message": "Nearby Places + Weather API",
  "endpoints": ["/nearby"]
}
```

---

### 2. Nearby places + weather

Returns up to **5 nearby places** of a given type and **current weather** for the given coordinates.

| Item        | Value        |
|------------|--------------|
| **Method** | `GET`        |
| **Path**   | `/nearby`    |
| **Params** | See below    |

#### Query parameters

| Parameter | Required | Default   | Description |
|-----------|----------|-----------|-------------|
| `lat`     | **Yes**  | —         | Latitude (e.g. `12.9716`) |
| `lon`     | **Yes**  | —         | Longitude (e.g. `77.5946`) |
| `type`    | No       | `cafe`    | Place type (see supported types below) |
| `radius`  | No       | `1000`    | Search radius in **meters** (e.g. `500`, `2000`) |

#### Supported place types

You can use any of these for the `type` parameter:

| Type        | Description     |
|-------------|-----------------|
| `cafe`      | Cafes           |
| `restaurant`| Restaurants     |
| `xerox`     | Print / copy shops |
| `copyshop`  | Same as xerox   |
| `atm`       | ATMs            |
| `pharmacy`  | Pharmacies      |
| `library`   | Libraries       |

Other keywords may work but are not guaranteed; the API maps them to Google Places types.

---

## What to send

- **Minimum:** `lat` and `lon` (numbers).
- **Optional:** `type` (string), `radius` (integer, in meters).

All parameters are sent as **query parameters** in the URL (no request body).

**Example URLs**

- Cafes within 1 km (default radius):  
  `.../nearby?lat=12.9716&lon=77.5946`
- Restaurants within 1.5 km:  
  `.../nearby?lat=12.9716&lon=77.5946&type=restaurant&radius=1500`
- ATMs within 500 m:  
  `.../nearby?lat=12.9716&lon=77.5946&type=atm&radius=500`

---

## What you get

### Success response (`200 OK`)

JSON body shape:

```json
{
  "location": {
    "lat": 12.9716,
    "lon": 77.5946
  },
  "placeType": "cafe",
  "radiusMeters": 1500,
  "weather": {
    "temperature": 28.5,
    "description": "clear sky"
  },
  "places": [
    {
      "name": "Coffee House",
      "lat": 12.9721,
      "lon": 77.5948,
      "distanceMeters": 85.3,
      "address": "123 MG Road, Bangalore",
      "source": "GooglePlaces"
    }
  ]
}
```

| Field            | Description |
|------------------|-------------|
| `location`       | Your requested `lat` / `lon`. |
| `placeType`      | The `type` you asked for. |
| `radiusMeters`   | The `radius` you asked for. |
| `weather`        | Current weather at that location. `temperature` is in Celsius. Can be `null` if the weather API is not configured or fails. |
| `places`         | Array of up to 5 nearby places, sorted by distance. Each has `name`, `lat`, `lon`, `distanceMeters`, `address`, and `source` (`"GooglePlaces"`). |

If no places are found, `places` is an empty array `[]`.  
If weather is unavailable, `weather` is `null`.

---

## Error responses

### Missing `lat` or `lon` — `400 Bad Request`

**Request:** `GET /nearby` (no params) or missing `lat`/`lon`

**Response:**

```json
{
  "error": "lat and lon are required query parameters"
}
```

### Invalid numbers — `400 Bad Request`

**Request:** e.g. `lat=abc` or `radius=not_a_number`

**Response:**

```json
{
  "error": "lat and lon must be numbers; radius must be an integer (meters)"
}
```

### Upstream failure (e.g. places provider) — `502 Bad Gateway`

**Response:**

```json
{
  "error": "Failed to fetch places from provider: ..."
}
```

Weather failures do not cause 502; the API still returns 200 with `weather: null`.

---

## How to call the API

### cURL

```bash
# Health check
curl "https://api.abhishekmudaraddi.com/"

# Nearby cafes (Bangalore example)
curl "https://api.abhishekmudaraddi.com/nearby?lat=12.9716&lon=77.5946&type=cafe&radius=1500"
```

### Browser

Paste the URL in the address bar (same URLs as above). You will see the JSON response.

### Postman / Insomnia

1. Method: **GET**
2. URL:  
   `https://api.abhishekmudaraddi.com/nearby?lat=12.9716&lon=77.5946&type=cafe&radius=1500`
3. No headers or body required. Send the request.

### From your own app (e.g. JavaScript)

```javascript
const baseUrl = "https://api.abhishekmudaraddi.com";
const lat = 12.9716;
const lon = 77.5946;
const type = "cafe";
const radius = 1500;

const url = `${baseUrl}/nearby?lat=${lat}&lon=${lon}&type=${type}&radius=${radius}`;

fetch(url)
  .then((res) => res.json())
  .then((data) => console.log(data))
  .catch((err) => console.error(err));
```

---

## Summary for integrators

| What you need | Value |
|---------------|--------|
| **Base URL** | `https://api.abhishekmudaraddi.com` |
| **Main endpoint** | `GET /nearby` |
| **Required params** | `lat`, `lon` (numbers) |
| **Optional params** | `type` (default `cafe`), `radius` (default `1000`, meters) |
| **Response** | JSON with `location`, `placeType`, `radiusMeters`, `weather`, `places` |

No API key or authentication is required to call this public API.

---

## Running locally (developers)

1. **Clone / go to project folder**

   ```bash
   cd SCALEAPP
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies**

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. **Set API keys (optional; without them, weather/places may be empty)**

   ```bash
   export OPENWEATHER_API_KEY="your_openweather_key"
   export GOOGLE_PLACES_API_KEY="your_google_places_key"
   ```

5. **Run the app**

   ```bash
   python app.py
   ```

   Server runs at `http://localhost:5000`. Use the same paths: `/` and `/nearby?lat=...&lon=...`.

6. **Test**

   ```bash
   curl "http://localhost:5000/"
   curl "http://localhost:5000/nearby?lat=12.9716&lon=77.5946&type=cafe"
   ```

---

## Deploying to AWS Elastic Beanstalk (optional)

If you deploy your own copy:

1. Install **EB CLI**: `python -m pip install awsebcli`
2. From the project folder: `eb init`, then `eb create` (or `eb use` an existing env).
3. In **AWS Console → Elastic Beanstalk → Configuration → Software**, add environment variables:
   - `OPENWEATHER_API_KEY`
   - `GOOGLE_PLACES_API_KEY`
4. Deploy: `eb deploy`

Then use your environment’s URL (e.g. from `eb status`) as the base URL in this README.

---

## Tech stack

- **Backend:** Python 3, Flask  
- **APIs:** Google Places (nearby search), OpenWeatherMap (current weather)  
- **Hosting:** AWS Elastic Beanstalk (Python 3.14 on Amazon Linux 2023)
