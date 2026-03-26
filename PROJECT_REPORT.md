# Cloud Application Integrating Multiple Web Services
**Author:** Abhishek Mudaraddi  
**Module:** Cloud Application Development  
**Date:** 2026

---

## Abstract

This project presents a cloud-based application solution that integrates and consumes multiple web application services through a user-facing dashboard and a custom backend API. The solution consists of two primary components: (i) a front-end Flask web application (`APP`) that collects user input and orchestrates service consumption, and (ii) a backend API service (`SCALEAPP`) deployed on AWS Elastic Beanstalk. The backend API receives geographic search parameters, validates and processes them, and returns nearby places enriched with weather information.

The overall solution integrates four external service categories to satisfy coursework requirements: a self-developed web service (`SCALEAPP`), a classmate-developed document compression API (AWS API Gateway endpoint), and public APIs including Google Places, OpenWeatherMap, and BigDataCloud reverse geocoding. The user can search nearby points of interest, view weather and geospatial context, and upload documents for compression with guided progress and download functionality.

The project also includes CI/CD automation via GitHub Actions, with test and deployment stages targeting AWS Elastic Beanstalk. HTTPS custom-domain routing and CORS handling were addressed to support cross-origin browser clients and real-world deployment conditions. Key outcomes include successful multi-service composition, operational public cloud deployment, and practical lessons in DNS, TLS certificate management, API integration reliability, and cloud DevOps workflows. The implementation demonstrates a production-oriented approach to integrating heterogeneous APIs while maintaining usability, modular design, and deployment repeatability.

---

## 1. Introduction

Modern cloud applications are increasingly composed from multiple APIs rather than built as monolithic systems. This project was motivated by the need to design and implement an end-to-end cloud solution that combines:

1. a custom backend API,  
2. third-party public APIs, and  
3. a peer-developed API service,

while providing a usable front-end interface and a public cloud deployment pipeline.

The core objective was to create a practical application where users can:
- search nearby places by latitude/longitude and place type,
- receive weather and location context,
- and compress uploaded PDF/DOCX files via a classmate API integration.

The project intentionally emphasizes cloud deployment realism: domain routing, HTTPS setup, CORS policies, environment variables, CI/CD automation, and integration troubleshooting. By implementing both API provider and API consumer roles, the work demonstrates interoperability and collaborative service consumption, which are central learning outcomes of the module.

---

## 2. Project Specification and Requirements

### 2.1 Coursework Requirement Mapping

| Coursework Requirement | Implementation Status | Evidence |
|---|---|---|
| Front-end application with user input | Implemented | `APP/templates/index.html` includes search form and file upload section |
| Consume 3-5 different web services | Implemented | Own API + classmate API + public APIs (Google Places, OpenWeatherMap, BigDataCloud) |
| One web service written by student | Implemented | `SCALEAPP` (`/`, `/nearby`) |
| At least one web service by classmate | Implemented | Compression API: `https://4ecpi9z5mj.execute-api.us-east-1.amazonaws.com/compress` |
| At least one public web service | Implemented | Google Places, OpenWeatherMap, BigDataCloud |
| Backend API receives/processes/responds meaningfully | Implemented | Input validation, type conversion, provider calls, merged JSON response |
| Backend designed for scalability | Partially evidenced | Deployed on AWS Elastic Beanstalk (managed platform with scaling support); autoscaling policy evidence should be added |
| Share API with classmates | Implemented | Public API URL and docs in `SCALEAPP/README.md` |
| Implement, test, and deploy to public cloud | Implemented | AWS Elastic Beanstalk + GitHub Actions pipeline |

### 2.2 Functional Scope

**User-facing features**
- Nearby search with latitude, longitude, place type, and radius.
- Result visualization including place list, weather, reverse-geocoded details, and map view.
- Document compression workflow with upload, progress steps, size comparison, and download.

**Backend features**
- Public REST endpoint for nearby-search aggregation.
- Error handling and meaningful status codes.
- CORS support for browser-based consumers.

---

## 3. Architecture and Design Aspects

### 3.1 High-Level Architecture

The system follows a composed-service cloud pattern:

1. **APP (Flask Web UI / API consumer)**  
   - Accepts user input.  
   - Calls own backend API (`SCALEAPP`) for nearby + weather data.  
   - Calls public reverse geocoding API (BigDataCloud).  
   - Proxies file upload to classmate compression API and returns downloadable output.

2. **SCALEAPP (Flask REST API / API provider)**  
   - Exposes `/` and `/nearby`.  
   - Calls Google Places and OpenWeatherMap.  
   - Processes data (distance sorting, response shaping) and returns merged JSON.

3. **External Services**
   - Google Places API (nearby search provider),
   - OpenWeatherMap (weather provider),
   - BigDataCloud (reverse geocoding),
   - Classmate compression API (document compression),
   - AWS services (Elastic Beanstalk, ACM, Route 53, GitHub Actions).

### 3.2 Design Patterns and Rationale

- **API Aggregator Pattern**: `SCALEAPP` aggregates place + weather into one response, reducing front-end coupling and request complexity.
- **Backend-for-Frontend Proxy Pattern**: `APP` proxies compression upload/download to isolate classmate API contract details and avoid client-side CORS/auth complexity.
- **Configuration via Environment Variables**: API URLs, keys, and CORS origins are externalized, improving deployment flexibility and security.
- **Graceful Degradation**: If weather fails, nearby data is still returned with `weather: null`.
- **Separation of Concerns**: UI orchestration (`APP`) and core geospatial API logic (`SCALEAPP`) are independently deployable concerns.

### 3.3 Cloud Justification

AWS Elastic Beanstalk was selected for:
- managed deployment of Python web apps,
- simplified operational setup,
- support for scaling and health monitoring,
- easy integration with custom domain and TLS.

This choice balances developer productivity and cloud realism for an academic project.

---

## 4. Implementation

### 4.1 Backend API (`SCALEAPP`)

**Tech stack:** Flask, requests, flask-cors.  
**Endpoint base URL:** `https://api.abhishekmudaraddi.com`

#### Endpoint 1: Health
- `GET /`
- Returns service status and available endpoints.

#### Endpoint 2: Nearby Search
- `GET /nearby?lat=...&lon=...&type=...&radius=...`
- Validates required parameters and numeric formats.
- Maps user place type to provider-specific keyword.
- Calls Google Places and OpenWeatherMap.
- Computes and sorts distances via haversine formula.
- Returns merged JSON:
  - `location`, `placeType`, `radiusMeters`, `weather`, `places`.

#### Error Handling
- 400 for missing/invalid inputs.
- 502 for upstream provider failures.
- Non-fatal weather fallback (`weather: null`) when weather retrieval fails.

#### CORS Support
`flask-cors` was added to return browser-compatible CORS headers, enabling third-party front-ends (e.g., localhost Live Server) to call the API.

### 4.2 Front-end Application (`APP`)

**Tech stack:** Flask templating + HTML/CSS/JavaScript.  
**Purpose:** User-facing multi-service orchestrator.

#### Nearby Search Flow
- User submits lat/lon/type/radius.
- App calls own API (`SCALEAPP /nearby`).
- App also calls BigDataCloud for location labels.
- Results displayed with weather summary, places list, metadata, and map.

#### Compression Flow (Classmate API Integration)
- User uploads PDF/DOCX from dashboard.
- `POST /compress` in `APP` receives file.
- Server forwards multipart upload to classmate endpoint:
  - `https://4ecpi9z5mj.execute-api.us-east-1.amazonaws.com/compress`
- Upstream response is returned as downloadable file.
- UI includes:
  - step-by-step progress checklist,
  - success/failure status,
  - original vs compressed size comparison,
  - download button.

#### UX Enhancements
- Input helper actions (current location, clear form).
- Compression progress states with visual indicators.
- Size reduction badge (percentage and bytes saved).

### 4.3 Security and Configuration

- API keys loaded from environment variables:
  - `GOOGLE_PLACES_API_KEY`
  - `OPENWEATHER_API_KEY`
  - optional `COMPRESS_API_KEY`
- Configurable upstreams:
  - `SCALEAPP_BASE_URL`
  - `COMPRESS_API_URL`
  - `COMPRESS_FILE_FIELD`
- CORS origin policy optionally controllable via `CORS_ORIGINS`.

No secrets are hardcoded in source code.

---

## 5. Continuous Integration, Delivery, and Deployment

### 5.1 GitHub Actions Pipeline

Workflow: **Test and Deploy APP** (`.github/workflows/pipeline.yml`)

#### Trigger
- Push/PR on `main` or `master`.

#### Jobs
1. **Test Job**
   - Python setup
   - Dependency install
   - App import check (`from app import app`)

2. **Deploy Job**
   - Runs after test on push events
   - Installs EB CLI
   - Configures AWS credentials via GitHub secrets
   - Debug step prints AWS identity and available EB environments
   - Executes `eb deploy app-env` in `APP` folder

### 5.2 Deployment Targets

- `APP` deployed to Elastic Beanstalk environment: `app-env`
- `SCALEAPP` deployed to Elastic Beanstalk environment: `nearby-api-env`
- Custom domains managed with Route 53 + ACM certificates for HTTPS.

### 5.3 Operational Issues Encountered and Resolved

- **Environment not found (`app-env`)** in CI:
  - resolved via identity/environment debug step and alignment of account/region/environment names.
- **DNS NXDOMAIN** after nameserver migration:
  - fixed by moving records to authoritative Route 53 zone.
- **HTTPS not reachable on custom subdomain**:
  - fixed by ACM certificate + ALB HTTPS listener + SG rule for port 443.
- **CORS browser failures**:
  - fixed by enabling CORS headers in `SCALEAPP`.

---

## 6. Testing and Validation

### 6.1 API-Level Tests
- Health endpoint validation (`GET /`).
- Nearby endpoint validation with required/optional params.
- Error-path tests for missing/invalid query values.
- Cross-origin browser tests after CORS change.

### 6.2 Integration Tests
- End-to-end Nearby flow from UI input to rendered result + map.
- Compression upload to classmate API and downloadable output verification.
- Size comparison output confirms observable compression behavior.

### 6.3 Deployment Validation
- GitHub Actions run logs for test/deploy stages.
- Public URL checks using browser and `curl`.
- Route and certificate verification for custom HTTPS domains.

---

## 7. Conclusions and Reflection

This project successfully implemented a cloud application that consumes multiple web services while exposing and sharing a custom backend API. The final solution demonstrates practical multi-API orchestration, front-end usability, deployment automation, and cross-origin interoperability. The architecture provides clear separation between UI orchestration (`APP`) and domain-specific backend processing (`SCALEAPP`), improving maintainability and extensibility.

A major learning outcome was that cloud integration success depends as much on infrastructure correctness (DNS, TLS listeners, security groups, CORS policy, CI credentials, environment names) as on application code. Several real-world incidents—such as environment mismatches and CORS blocking—reinforced the need for systematic diagnostics and observability in deployment pipelines.

From a scalability perspective, deployment on Elastic Beanstalk provides a managed base with scaling capabilities. For stronger enterprise-grade scalability, future work should include explicit autoscaling policy documentation, asynchronous processing (queues) for file-heavy workflows, and load/performance benchmarking.

Overall, the project met the core module objectives and provided valuable experience in collaborative API ecosystems, cloud operations, and iterative debugging of distributed web applications.

---

## 8. References (IEEE Style)

[1] IEEE, “IEEE Conference Template,” IEEE Author Center. [Online]. Available: https://www.ieee.org/conferences/publishing/templates.html. [Accessed: Mar. 24, 2026].

[2] Pallets, “Flask Documentation,” 2026. [Online]. Available: https://flask.palletsprojects.com/. [Accessed: Mar. 24, 2026].

[3] C. Dolphin et al., “Flask-CORS Documentation,” 2026. [Online]. Available: https://flask-cors.readthedocs.io/. [Accessed: Mar. 24, 2026].

[4] Google, “Places API (Nearby Search),” Google Maps Platform. [Online]. Available: https://developers.google.com/maps/documentation/places/web-service/search-nearby. [Accessed: Mar. 24, 2026].

[5] OpenWeather, “Current Weather Data API,” 2026. [Online]. Available: https://openweathermap.org/current. [Accessed: Mar. 24, 2026].

[6] BigDataCloud, “Reverse Geocoding API,” 2026. [Online]. Available: https://www.bigdatacloud.com/geocoding-apis/reverse-geocode-to-city-api. [Accessed: Mar. 24, 2026].

[7] Amazon Web Services, “AWS Elastic Beanstalk Developer Guide,” 2026. [Online]. Available: https://docs.aws.amazon.com/elasticbeanstalk/. [Accessed: Mar. 24, 2026].

[8] Amazon Web Services, “Amazon Route 53 Developer Guide,” 2026. [Online]. Available: https://docs.aws.amazon.com/route53/. [Accessed: Mar. 24, 2026].

[9] Amazon Web Services, “AWS Certificate Manager User Guide,” 2026. [Online]. Available: https://docs.aws.amazon.com/acm/. [Accessed: Mar. 24, 2026].

[10] GitHub, “GitHub Actions Documentation,” 2026. [Online]. Available: https://docs.github.com/actions. [Accessed: Mar. 24, 2026].

---

## Appendix A (Suggested Evidence to Add Before Final Submission)

- Screenshot of front-end showing:
  - Nearby query input + results,
  - compression section,
  - size comparison and download button.
- Screenshot of public API response (`/nearby`) in browser/Postman.
- Screenshot of GitHub Actions successful test + deploy run.
- Screenshot of EB environments (`app-env` and `nearby-api-env`) health status.
- Screenshot of Route 53 record(s) and ACM certificate status (Issued).
- Optional: screenshot of CORS response headers in browser network tab.
