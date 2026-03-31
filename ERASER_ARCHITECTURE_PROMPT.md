# Eraser.io Architecture Prompt for This Project

Use the following prompt directly in Eraser.io AI Diagram to generate a simple, informative architecture diagram for this project.

---

## Prompt to Paste in Eraser.io

Create a clear cloud architecture diagram for a project called **ScalableProject**.

The diagram must be simple, easy to understand, and show API integrations clearly.

Use left-to-right flow with these sections:

1. **User Layer**
   - User (Web Browser)

2. **Frontend Application Layer**
   - `APP` (Flask Web Application, AWS Elastic Beanstalk: `app-env`)
   - Label APP features:
     - Planner tab (nearby search + map + images)
     - API Playground
     - PDF generation and compression flow
     - Image operation controls

3. **Backend API Layer**
   - `SCALEAPP` (Flask Scalable API, AWS Elastic Beanstalk: `nearby-api-env`)
   - Main endpoint: `GET /nearby`
   - Show processing in SCALEAPP:
     - Validate inputs (`lat`, `lon`, `type`, `radius`)
     - Call external APIs
     - Compute distance (haversine)
     - Return normalized JSON response

4. **External API Integrations**
   - Google Places API (nearby places + photo references)
   - OpenWeatherMap API (weather data)
   - BigDataCloud Reverse Geocoding API (location details)
   - Classmate Image API (upload/transform image)
   - Classmate Compression API (compress PDF/DOCX)

5. **Cloud and DevOps Layer**
   - AWS Route 53 (DNS)
   - AWS ACM (SSL/TLS certificates)
   - HTTPS custom domain routing to APP/SCALEAPP
   - AWS CloudWatch Dashboard (metrics/log monitoring for both APP and SCALEAPP)
   - GitHub Actions CI/CD Pipeline:
     - Test stage
     - SonarQube/SonarCloud static analysis + quality gate
     - Deploy APP to Elastic Beanstalk

6. **Planner PDF Sub-flow (inside APP)**
   - User clicks "Generate original + compressed PDFs"
   - APP generates original PDF (with place details, weather, and images)
   - APP calls classmate compression API
   - APP returns both:
     - Original PDF
     - Compressed PDF
   - Show size comparison output

Diagram style requirements:
- Keep it minimal and readable (no clutter).
- Use grouped containers for each layer.
- Use directional arrows with labels like "REST API", "HTTPS", "CI/CD", "Monitoring".
- Highlight that SCALEAPP is the **student-developed scalable API** and APP is the **integration/demonstration application**.
- Include a small legend for icons/colors.

---

## Suggested Diagram Title

**Cloud Architecture - ScalableProject (APP + SCALEAPP with Multi-API Integration)**

---

## Optional Quick Variant Prompt (Short)

Draw a simple cloud architecture for a Flask-based project with two apps: `APP` (frontend integration app on Elastic Beanstalk `app-env`) and `SCALEAPP` (scalable backend API on Elastic Beanstalk `nearby-api-env`). Show user browser -> APP -> SCALEAPP and external APIs (Google Places, OpenWeatherMap, BigDataCloud, classmate image API, classmate compression API). Include Route53 + ACM HTTPS, CloudWatch monitoring for both apps, and GitHub Actions CI/CD with Sonar static analysis + quality gate before deploy. Also show planner PDF flow in APP: generate original PDF, compress via classmate API, return original + compressed download.
