# Cloud Application Integrating and Consuming Web Services
**Author:** Abhishek Mudaraddi  
**Module:** Cloud Application Development  
**Date:** 2026

---

## Abstract

This report presents the full lifecycle development of a cloud application solution that integrates and consumes multiple web application services through a two-part architecture. The first part is `SCALEAPP`, a backend REST API implemented as the author’s own web service and treated as the scalable service layer. The second part is `APP`, a user-facing integration application that demonstrates service consumption and orchestration through a planner workflow, API playground features, image operations, and PDF export/compression. The project satisfies the module requirement to combine one self-developed service, classmate-developed services, and publicly available services, and to deploy and operate the result in a public cloud environment. The final integrated stack uses Google Places API for nearby search, OpenWeatherMap for weather context, BigDataCloud for reverse geocoding, a classmate image API for transformation workflows, and a classmate compression API for document compression, with application deployment on AWS Elastic Beanstalk and operational visibility through CloudWatch [3]-[7].

The implementation emphasizes meaningful backend processing, not simple pass-through calls. `SCALEAPP` validates request parameters, maps category inputs, queries provider endpoints, computes geodesic distance, sorts results, and normalizes response payloads for consumer clients. `APP` acts as an orchestration and demonstration layer that integrates all APIs into coherent user journeys and preserves usability through progressive status updates, map views, and downloadable planner artifacts. Delivery and reliability are strengthened through GitHub Actions CI/CD and static analysis integration using SonarQube/SonarCloud quality gates [8], [9]. The project also addresses practical cloud engineering challenges such as HTTPS configuration, DNS correctness, CORS compatibility, and environment-based secret management. The main results show that a modular API-driven architecture can satisfy coursework functionality while also demonstrating realistic DevOps and cloud operations practices. The report concludes with technical findings, design trade-offs, and reflective lessons learned from building and hardening an integration-heavy cloud system.

---

## 1. Introduction

### 1.1 Motivation

The motivation for this project emerged from the way modern cloud systems are actually built in industry. Most production applications are no longer monolithic implementations developed from scratch; instead, they combine internal APIs, partner APIs, and public APIs into one user-facing experience. This integration-driven model introduces specific engineering concerns that are often more difficult than writing baseline logic, including cross-service contracts, resilient error handling, endpoint observability, runtime configuration, and controlled release pipelines. The project was therefore designed not only to satisfy module functionality, but to intentionally expose these cloud integration realities and to produce an artifact that demonstrates both software construction and cloud operations competence [2], [6], [9].

### 1.2 Main Objectives

The assignment requirement to build a front-end application consuming multiple services and a meaningful backend web service naturally suggested a split architecture. The backend service in this project is `SCALEAPP`, which is the author-developed API intended to be shared with classmates as a reusable nearby-place provider. The front-end integration and demonstration layer is `APP`, which consumes the author’s API, classmate APIs, and public APIs. This separation was not just organizational convenience; it was a strategic architecture decision to preserve the stability of the shared API while allowing rapid evolution of end-user experience in the application layer. In practical terms, classmates can call `SCALEAPP` without being coupled to experimentation in `APP`, and `APP` can add planner-centric features without forcing breaking changes in the core API contract.

### 1.3 User Journey Context

The main objective of the project was to create a cloud-hosted planner experience where user input drives a chain of API calls that return interpretable and actionable results. The user selects a category such as cafe, gym, pharmacy, or restaurant, location is obtained from browser geolocation, nearby results are fetched, weather context is added, and details are rendered with map markers and images. The same result set can then be processed further through image operations and converted into downloadable planner documents in original and compressed forms. This objective made it possible to validate the assignment’s integration requirement in a traceable manner: each major user action maps to one or more service invocations and demonstrates concrete API composition.

### 1.4 Operational Goals

Beyond raw functionality, the project also set explicit operational objectives. These included deployment to a public cloud environment, HTTPS-ready routing, observability through CloudWatch, and CI/CD automation in GitHub Actions. Static analysis integration through SonarQube/SonarCloud was added to ensure that code quality checking became part of routine delivery and not an optional post-development activity. Taken together, the project objective was broader than building a single app screen; it was to establish a practical, testable, deployable, and monitorable cloud service ecosystem consistent with modern engineering workflows.

---

## 2. Project Specification and Requirements

### 2.1 Requirement Interpretation

The formal project brief required the implementation of a cloud application that integrates multiple web services through a front-end interface and includes one self-developed backend API. It also required that at least one integrated service be developed by a classmate and at least one be publicly available. In addition, the backend service had to receive input, perform meaningful processing, and return useful responses rather than simply relaying external results. Finally, the service had to be designed with scalability in mind and deployed to a public cloud platform. The implemented solution was planned directly around these constraints so that each requirement could be mapped to explicit design and implementation decisions.

### 2.2 Requirement-to-Implementation Mapping

The front-end requirement was satisfied through `APP`, a Flask-based user interface that accepts planner input and supports multiple interactive operations. The custom backend requirement was satisfied through `SCALEAPP`, an independently deployed API service exposing nearby-place functionality. The classmate API requirement was met through two integrations: an image processing service and a document compression service. The public API requirement was met through Google Places (place discovery), OpenWeatherMap (weather context), and BigDataCloud (reverse geocoding). This combination results in a service graph where each external call has a clear functional role and the end-to-end workflow remains coherent to the user.

### 2.3 Meaningful Backend Processing Requirement

Meaningful processing in the custom backend was interpreted rigorously. The backend validates parameters, resolves defaults, handles malformed input, queries upstream services, performs geospatial distance computation using haversine calculation, sorts candidate places by proximity, and shapes an application-specific response contract. The result is a stable consumer-facing API model that abstracts external provider complexity. This processing layer improves reuse and ensures the service can be shared with classmates in a predictable form, consistent with the assignment requirement to publish a usable API.

### 2.4 Scalability Requirement

Scalability in this project was addressed through both architecture and deployment strategy. Architecturally, `SCALEAPP` is stateless and request-driven, which is compatible with horizontal scaling. Operationally, it is deployed to Elastic Beanstalk, a managed platform that supports load-balanced and scalable Python web applications [6]. While full-scale synthetic load testing is beyond current scope, the service design avoids sticky session coupling and uses externalized configuration, making it suitable for incremental scaling. The project therefore interprets scalability as a realistic foundation rather than a theoretical claim.

### 2.5 Cloud Deployment and Verification Requirement

The final requirement on implementation, testing, and public deployment was satisfied through cloud deployment and CI/CD integration. `APP` and `SCALEAPP` were deployed to public AWS environments, domain and TLS issues were resolved with Route 53 and ACM [10], and a GitHub Actions workflow was configured to test, analyze, and deploy code. The SonarQube/SonarCloud integration added quality gates to static analysis, reinforcing a release governance model where delivery depends on passing quality checks [8], [9]. This requirement mapping confirms that the project is not only functionally complete but aligned with software engineering discipline expected by the module.

---

## 3. Architecture and Design Aspects of the Application

### 3.1 Selected Cloud Architecture

The selected architecture follows a producer-consumer cloud composition model, with strict role separation between the scalable API provider and the orchestration application. In this model, `SCALEAPP` is positioned as a reusable backend API whose primary responsibility is geospatial intelligence, while `APP` is positioned as the integration gateway for end-user workflow. This architecture was chosen after considering two alternatives: embedding all logic in one front-end server, or exposing direct browser access to all third-party APIs. The monolithic option was rejected because it would reduce API shareability and blur responsibility boundaries. The direct-browser option was rejected because it introduces key management, CORS complexity, and fragile client dependency on multiple provider contracts.

### 3.2 Layered Design Structure

The resulting architecture can be understood as a layered composition. At the data-provider layer, public APIs and classmate APIs expose specialized functionality. At the service layer, `SCALEAPP` and selected server-side proxy routes in `APP` normalize and secure access to these providers. At the presentation layer, the planner interface coordinates user input, displays results, and exposes progressive operations such as image processing and PDF export. This layering is critical for maintainability because each layer evolves with different change frequency. Provider APIs may change formats, service logic may change aggregation behavior, and UI may change interaction style, but interface contracts can be preserved at layer boundaries.

### 3.2.1 Architecture Diagram Explanation

The architecture diagram included in this report visually represents the operational flow of the developed system from user request to multi-API response and deployment governance. The flow begins with the user in a web browser sending HTTPS requests through Route 53 and SSL/TLS configuration to the deployed `APP` environment in AWS. `APP` acts as the integration and orchestration layer: it handles UI interactions, forwards nearby-search calls to `SCALEAPP`, invokes classmate APIs for image operations and PDF compression, and coordinates planner artifact generation. `SCALEAPP`, shown as a separate backend environment, performs the core geospatial processing by consuming Google Places for place discovery and photo references, OpenWeatherMap for weather enrichment, and BigDataCloud for reverse geocoding context. The diagram also highlights that both APP and scalable API components are monitored through CloudWatch logs and metrics, allowing runtime visibility for request behavior and failure diagnostics. On the top control plane, GitHub Actions and Sonar analysis are linked to show that code changes are statically analyzed and quality-gated before deployment to cloud environments. This representation is intentionally simple but informative: it demonstrates clear separation of concerns, explicit API integration paths, secure public ingress, CI/CD-controlled deployment, and observability coverage. In academic terms, the diagram supports the project argument that the solution is not only functionally integrated but also architected for maintainability, deployability, and scalable service composition.

### 3.3 Design Patterns and Justification

A key design pattern implemented in `SCALEAPP` is an API aggregation pattern. Instead of forcing front-end clients to issue separate requests to nearby place providers and weather providers and then perform local joins, the backend API combines these calls and returns a single normalized response object. This pattern reduces request fan-out, centralizes validation, and keeps consumer logic simpler. Another pattern used in `APP` is backend-for-frontend proxying for classmate services. By routing file-heavy operations through application backend endpoints, the design avoids exposing integration details and supports better centralized error reporting.

### 3.4 Configuration and Resilience Decisions

Configuration strategy follows a twelve-factor style approach where runtime variables define API keys, base URLs, and optional secrets. This allows development, test, and production environments to remain code-consistent while still supporting different credentials and endpoint mappings. The architecture also uses explicit fallback behavior for non-critical dependency failures. For example, failure in one provider path should not necessarily collapse the entire request unless the failed data is mandatory for user value. This resilience-oriented behavior was particularly important in an integration-heavy application where upstream services may occasionally throttle or return transient errors.

### 3.5 Scalability and Observability Analysis

The scalability aspect of architecture is supported through stateless API behavior and managed cloud deployment. `SCALEAPP` does not depend on local session state and can be replicated behind load balancing. Elastic Beanstalk offers deployment abstractions compatible with autoscaling patterns, health checks, and controlled releases [6]. CloudWatch was integrated to observe system behavior across both APP and scalable API environments, including request-level and instance-level metrics [7]. This observability layer supports architectural verification: if scaling or reliability assumptions fail, they can be detected through telemetry rather than guessed.

### 3.6 Trade-offs and Future Architecture Improvements

From a critical perspective, the current architecture is strong for assignment scale but has identifiable future-growth constraints. Synchronous API chaining for all operations can introduce latency compounding when provider response times vary. PDF generation and image processing are currently synchronous request workflows and may benefit from queue-based decoupling in higher-volume scenarios. A future architecture could introduce asynchronous worker patterns, object storage staging, and event-driven orchestration for heavy tasks. However, for the scope of this project, the chosen architecture provides an appropriate balance between implementation complexity, demonstrable scalability, and coursework objectives.

### 3.7 Contract Stability and Compatibility

An additional architectural consideration is service contract stability. Because external providers evolve independently, the internal response contract exposed by `SCALEAPP` becomes a protective compatibility layer. In practical terms, if Google Places changes optional fields or response ordering, consumer clients do not need immediate rewrite so long as `SCALEAPP` keeps its own output schema stable. This reduces downstream disruption and is one reason API ownership boundaries were treated as first-class design concerns. The same principle applies in `APP`, where proxy routes isolate classmate API variability from browser logic. In a cloud-integration context, this approach is effectively a form of anti-corruption layer, preventing direct provider schema drift from leaking into user-facing code.

### 3.8 Cost and Performance Considerations

Cost and performance trade-offs were also considered. Calling multiple APIs per user action can increase latency and cost variability, especially when provider quotas or network conditions are unstable. The architecture therefore favors minimal but meaningful aggregation in the scalable API and selective orchestration in the application layer, rather than adding unnecessary hops. This trade-off preserves responsiveness while still keeping responsibilities separated. In future iterations, selective caching of location-weather pairs and short-lived place query results could reduce repeated provider calls for nearby users without violating freshness expectations. Such caching strategies were identified but deferred to maintain assignment scope clarity.

---

## 4. Implementation

### 4.1 Development Phasing Approach

Implementation was completed in incremental phases, starting with core API construction and then evolving into a richer integration platform. The first phase implemented `SCALEAPP` as a Flask REST service exposing a nearby-search endpoint. Input parameters include latitude, longitude, place type, and radius. The implementation validates required fields, enforces numeric parsing, and returns structured errors for invalid requests. Once validated, the service calls Google Places API for location candidates and OpenWeatherMap for weather context [3], [4]. Provider responses are normalized into a single result schema and sorted using haversine-based distance logic. This creates a meaningful and reusable API layer rather than exposing provider-specific raw payloads directly.

### 4.2 APP Frontend and Planner Workflow

The second phase implemented `APP` as a Flask-rendered application with a tabbed interface to demonstrate integrated API workflows. The Planner tab became the core user journey. The interface captures a category string, uses browser geolocation to obtain coordinates, and requests nearby results. Returned places include name, rating, distance, coordinates, source metadata, and image URLs. Reverse geocoding data is fetched using BigDataCloud [5] to produce human-readable locality details. The planner map is rendered with Leaflet and places markers for both user location and nearby results. Additional tuning was added so map bounds recenter correctly when content visibility changes dynamically.

### 4.3 Weather Integration in UI and Export

Weather data is surfaced at two levels. First, weather is displayed directly in planner result context for immediate interpretation. Second, weather is included in generated planner documents so exported artifacts preserve environmental context from the search moment. This dual rendering ensures parity between on-screen analysis and offline sharing.

### 4.4 Image Processing Integration

Image integration was implemented through classmate API routes exposed via `APP` proxy endpoints. Planner results include images that can be transformed in batch mode based on selected operations and operation parameters. Supported transformations include grayscale, blur, rotate, resize, crop, and text overlays, with dynamic parameter field rendering based on action selection. A deliberate usability addition is a revert mechanism that restores original planner images after transformations. This was necessary because repeated transformations are destructive from user perspective; preserving a baseline snapshot gives users control and reduces the need for repeated searches.

### 4.5 PDF Generation and Compression Flow

Document generation and compression were implemented as a complete planner output pipeline. `APP` generates an original PDF that includes selected planner details and images using a server-side PDF library [2]. This original PDF is then sent to a classmate compression API and returned as a second downloadable output. The interface presents processing steps inline and provides size comparison between original and compressed files so users can verify compression impact immediately. The output panel includes both links because compression effectiveness can vary based on image-heavy source content.

### 4.6 Frontend State Management and UX Reliability

The implementation includes careful state management in the planner UI. When users execute a new search category, prior PDF generation state, prior download links, and prior comparison data are cleared. This prevents stale artifacts from being misinterpreted as outputs from newer search contexts. Similar state-reset logic is applied to image operation panels and status messages.

### 4.7 Security and Runtime Reliability

Security and reliability were addressed through environment-based configuration and controlled proxying. Sensitive values such as API tokens are read from environment variables rather than source files. Outbound API calls are wrapped in exception handling with explicit error responses so integration failures are observable and do not silently corrupt output state. CORS compatibility was enabled in the scalable API to support browser clients and classmate consumption. These details were not cosmetic; they were required to ensure that the application behaves predictably in distributed network conditions.

### 4.8 Detailed API Usage Summary

The final implementation therefore demonstrates more than a set of endpoints. It demonstrates end-to-end orchestration across heterogeneous services, user-state consistency under iterative operations, and practical cloud-oriented software behavior under changing integration conditions.

From an API usage perspective, each integrated service plays a distinct and traceable role. Google Places API is used for nearby entity discovery from location and keyword constraints, and the returned coordinates are then used to calculate true distance ordering in the project API [3]. OpenWeatherMap is used to provide contextual weather values for the same location point, which improves interpretability of planner choices in realistic use cases such as walking routes or outdoor destinations [4]. BigDataCloud reverse geocoding is used to convert raw coordinates into locality-level labels that are easier for users to understand and include in generated documents [5]. The classmate image API is used after place discovery to provide optional transformation workflows directly on planner result images, making the application demonstrably collaborative rather than purely public-API based. The classmate compression API is used at the final artifact stage to show a complete processing pipeline from data search to export optimization. This explicit role separation by API was intentional so that the report can clearly demonstrate compliance with requirement categories and provide a technically explainable integration map.

### 4.9 Iterative Fixes and Quality Improvements

Implementation quality also improved through iterative defect correction. Several interaction-level issues were resolved after real usage tests, including incorrect tab persistence, map centering behavior in dynamic containers, stale PDF state between searches, and missing clarity in processing status. Each fix required coordinated adjustments across state variables, rendering logic, and network call sequencing. These changes are important findings because they show that integration projects often fail at workflow edges rather than at core endpoint logic. Addressing these edges produced a more robust application and made user outcomes reproducible.

---

## 5. Continuous Integration, Delivery and Deployment of the Application

### 5.1 CI/CD Pipeline Structure

Delivery engineering was handled through a GitHub Actions pipeline designed around a test-before-deploy principle. The pipeline installs dependencies, verifies that application imports are valid, executes static code analysis, and only then permits deployment. This sequence is intentionally conservative and reflects the project's objective to treat deployment as a controlled release process rather than a manual upload step [9]. The deployment target is AWS Elastic Beanstalk for the application environment, while the scalable API is maintained as its own cloud service environment. This split aligns with the architectural separation between demonstration layer and reusable API layer.

### 5.2 SonarQube/SonarCloud Integration

Static analysis integration was completed through SonarQube/SonarCloud scanner actions and quality gate checks in the test stage [8]. This addition materially improved pipeline value because it introduced objective quality criteria beyond syntactic correctness. During integration, two practical issues were encountered and resolved: the first was missing `sonar.organization` configuration, and the second was conflict between CI analysis and SonarCloud automatic analysis mode. Resolving these issues required correct project properties, secure token/organization configuration in secrets, and disabling automatic analysis so CI remained the authoritative analysis path. This troubleshooting process provided a practical lesson in toolchain governance and eliminated ambiguity in quality reporting.

### 5.3 Public Cloud Deployment Configuration

Deployment to public cloud required infrastructure-level configuration alongside code release. Elastic Beanstalk environments were verified for correct naming and account-region alignment, and deployment diagnostics were added to workflow logs to expose identity and environment status. Custom domain and HTTPS configuration were implemented through Route 53 and ACM, with listener and certificate validation steps to ensure public endpoint reachability over TLS [10]. These steps were necessary because deployment correctness is determined not only by successful pipeline completion, but by actual public accessibility and certificate trust.

### 5.4 CloudWatch Monitoring and Operations

Operational monitoring was integrated through CloudWatch dashboards and service logs [7]. The dashboard design included both application and API contexts so that upstream and downstream behaviors could be interpreted together. This is particularly important in integration-heavy applications where errors can originate in either producer or consumer layers. By combining CI quality gates and runtime telemetry, the project established a practical continuous delivery loop: code is checked, released, observed, and iteratively improved.

### 5.5 Delivery Process Critique and Improvements

From a critical analysis perspective, the CI/CD design is effective for assignment scale, but there are clear opportunities for future hardening. Potential improvements include branch protection rules tied to quality gate status, artifact versioning for generated assets, automated rollback scripts, and smoke tests executed against deployed URLs post-release. Nevertheless, the implemented workflow demonstrates a complete and functioning pipeline from source control to monitored cloud runtime.

Another important delivery insight is that static analysis integration should be treated as part of system architecture, not as an external reporting add-on. By running Sonar checks before deployment and coupling deployment progression to quality gate outcomes, the pipeline enforces a minimum quality baseline in the same path used for release. This shifts quality from documentation to mechanism. The initial scanner setup issues and their resolution provided practical experience in CI toolchain governance, secret management, and cloud-hosted analyzer behavior. Once stabilized, the integration improved confidence that structural code issues would be detected early, reducing the risk of quality degradation through fast iteration.

The cloud deployment workflow also emphasized repeatability. Manual one-off deployment can appear faster initially but often leads to configuration drift and inconsistent runtime states. The GitHub Actions-driven approach improved consistency by making deployment behavior explicit and replayable. This proved useful when troubleshooting environment name mismatches and account-region alignment problems. Having deterministic deployment scripts and debug steps made root-cause analysis significantly faster than ad hoc cloud console actions. In educational settings, this repeatability is especially valuable because it produces auditable evidence of engineering process maturity.

---

## 6. Conclusions Including Findings/Interpretations

### 6.1 Outcome Summary

This project delivered a complete cloud application solution that satisfies the assignment specification while demonstrating practical cloud engineering depth. The implemented system integrates a self-developed scalable API (`SCALEAPP`), classmate APIs, and public APIs into a cohesive user experience in `APP`. The final artifact is not a prototype with disconnected features; it is a deployed, monitored, and quality-gated platform in which service boundaries, user workflows, and operational controls are aligned.

### 6.2 Key Technical Findings

The most important technical finding is that architectural separation strongly influences project success in integration-heavy systems. Treating `SCALEAPP` as a reusable API provider and `APP` as a consumer/orchestration layer enabled stable sharing with classmates and iterative enhancement of front-end functionality. Without this separation, changes in planner behavior, map rendering, image workflows, and PDF pipelines would likely have caused contract instability and increased regression risk. The producer-consumer model therefore proved to be both technically sound and pedagogically valuable.

A second major finding is that non-functional work is not secondary in cloud projects. DNS authority, HTTPS certificate wiring, security group rules, CORS headers, CI secret configuration, and analysis-mode settings all had direct impact on whether functionality was actually usable. In several stages, infrastructure or pipeline issues blocked otherwise correct application logic. Resolving these issues highlighted that cloud software quality is a combined property of code, configuration, and operations, not code alone.

A third finding concerns reliability under multi-API orchestration. Integrating public and classmate endpoints introduced variable response behavior, making explicit error handling and status propagation essential. User-facing improvements such as inline step visibility, revert options, and output comparison were not purely UX decoration; they improved transparency and trust in asynchronous or multi-stage operations. This became especially clear in PDF generation/compression workflows where users need evidence that processing actually occurred.

### 6.3 Reflection on Development Process

Reflection on the development process indicates strong growth in iterative engineering practice. Initial versions focused on functional output, while later versions emphasized robustness, observability, and release quality. Integrating SonarQube/SonarCloud into CI changed coding discipline by making static analysis outcomes visible and actionable before deployment. Integrating CloudWatch changed debugging behavior by shifting diagnosis from local assumption to runtime evidence. These additions transformed the project from a feature checklist into a full lifecycle cloud delivery exercise.

### 6.4 Future Work

There are still meaningful future directions. The current system can be strengthened by formal performance testing and explicit autoscaling policy documentation for `SCALEAPP`, queue-backed asynchronous processing for heavy image/PDF operations, stronger contract tests between producer and consumer services, and additional security controls such as stricter origin policies and secrets rotation automation. Even without these enhancements, the present project demonstrates a credible, deployable, and maintainable cloud application architecture that fulfills the module’s core intent: building, integrating, sharing, and operating API-driven services in a public cloud environment.

The personal reflection from this project is that cloud development is fundamentally iterative and socio-technical. Technical correctness alone was insufficient; many successful outcomes depended on communication with classmates about API contracts, interpretation of cloud platform diagnostics, and disciplined adjustment of deployment and analysis settings. The experience also reinforced that software quality is multidimensional. A feature can be correct functionally but still fail operationally due to deployment friction, or fail maintainability goals due to insufficient code quality controls. Integrating observability and static analysis into daily workflow changed development behavior from "build then check" to "build with checks in mind." This mindset shift is likely the most valuable learning outcome of the project, and it directly supports future work in production-scale cloud engineering.

---

## References (IEEE Style)

[1] IEEE, “IEEE Conference Template,” IEEE Author Center. [Online]. Available: https://www.ieee.org/conferences/publishing/templates.html. [Accessed: Mar. 26, 2026].  
[2] Pallets, “Flask Documentation.” [Online]. Available: https://flask.palletsprojects.com/. [Accessed: Mar. 26, 2026].  
[3] Google, “Places API (Nearby Search),” Google Maps Platform. [Online]. Available: https://developers.google.com/maps/documentation/places/web-service/search-nearby. [Accessed: Mar. 26, 2026].  
[4] OpenWeather, “Current Weather Data API.” [Online]. Available: https://openweathermap.org/current. [Accessed: Mar. 26, 2026].  
[5] BigDataCloud, “Reverse Geocoding API.” [Online]. Available: https://www.bigdatacloud.com/geocoding-apis/reverse-geocode-to-city-api. [Accessed: Mar. 26, 2026].  
[6] Amazon Web Services, “AWS Elastic Beanstalk Developer Guide.” [Online]. Available: https://docs.aws.amazon.com/elasticbeanstalk/. [Accessed: Mar. 26, 2026].  
[7] Amazon Web Services, “Amazon CloudWatch User Guide.” [Online]. Available: https://docs.aws.amazon.com/cloudwatch/. [Accessed: Mar. 26, 2026].  
[8] SonarSource, “SonarQube and SonarCloud Documentation.” [Online]. Available: https://docs.sonarsource.com/. [Accessed: Mar. 26, 2026].  
[9] GitHub, “GitHub Actions Documentation.” [Online]. Available: https://docs.github.com/actions. [Accessed: Mar. 26, 2026].  
[10] Amazon Web Services, “AWS Certificate Manager User Guide.” [Online]. Available: https://docs.aws.amazon.com/acm/. [Accessed: Mar. 26, 2026].  
[11] Amazon Web Services, “Amazon Route 53 Developer Guide.” [Online]. Available: https://docs.aws.amazon.com/route53/. [Accessed: Mar. 26, 2026].  
[12] Leaflet, “Leaflet JavaScript Library for Interactive Maps.” [Online]. Available: https://leafletjs.com/. [Accessed: Mar. 26, 2026].
