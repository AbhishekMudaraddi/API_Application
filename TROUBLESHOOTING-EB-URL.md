# Troubleshooting: Cannot Reach Nearby API (Elastic Beanstalk URL)

If **http://nearby-api-env.eba-z23r7ruf.us-east-1.elasticbeanstalk.com/** shows “site can’t be reached” or doesn’t load, work through these steps.

---

## 1. Use HTTP, Not HTTPS

The environment is set up for **HTTP** by default. Use:

- **Correct:** `http://nearby-api-env.eba-z23r7ruf.us-east-1.elasticbeanstalk.com/`
- **Wrong:** `https://...` (will often fail with “can’t be reached” or certificate errors)

Type `http://` explicitly in the browser.

---

## 2. Check Environment Status in AWS

The **nearby-api-env** Elastic Beanstalk environment might be stopped or unhealthy.

1. Log in to **AWS Console** → **Elastic Beanstalk**.
2. Region: **us-east-1** (N. Virginia).
3. Open application **SCALEAPP** → environment **nearby-api-env**.
4. Check **Environment health**:
   - **Ready** (green) – environment is running.
   - **Severe** / **Degraded** – check **Events** and **Health** for errors.
   - **Stopped** – start it: **Actions** → **Restart app server(s)** or **Resume environment** (if you had stopped it).

If the environment was **terminated**, the URL will no longer work; you’d need to create and deploy a new environment and update the URL in the app.

---

## 3. “Site Can’t Be Reached” (Connection / DNS)

If the browser says the site can’t be reached (no response at all):

- **Network/firewall:** Try another network (e.g. mobile hotspot or different Wi‑Fi). Some corporate or school networks block `*.elasticbeanstalk.com` or outbound HTTP.
- **DNS:** Try opening the URL on another device or after flushing DNS (e.g. `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` on macOS).
- **From terminal:** Run:
  ```bash
  curl -v http://nearby-api-env.eba-z23r7ruf.us-east-1.elasticbeanstalk.com/
  ```
  - If you see a response (even an error like 403), the host is reachable and the problem is likely app/config (see below).
  - If you see “Connection refused”, “Connection timed out”, or “Could not resolve host”, the issue is network/DNS or the environment is down.

---

## 4. Getting 403 Forbidden

If the site loads but returns **403 Forbidden**:

- The environment is up; something in the app or AWS is denying access.
- **Security groups:** In EC2 → Security Groups, ensure the one attached to the EB environment allows **inbound HTTP (port 80)** from `0.0.0.0/0` (or your IP) on the load balancer.
- **Application:** Check that your app serves the root path `/` and that it’s not returning 403 by design (e.g. missing or invalid auth).

---

## 5. Redeploy SCALEAPP (If You Have EB CLI)

From the **SCALEAPP** directory:

```bash
cd SCALEAPP
eb status
eb health
```

If the environment is **Ready**, try a fresh deploy:

```bash
eb deploy nearby-api-env
```

Then open again:  
**http://nearby-api-env.eba-z23r7ruf.us-east-1.elasticbeanstalk.com/**

---

## Summary

| Symptom | What to do |
|--------|------------|
| “Site can’t be reached” | Use **http**, check EB environment is **Ready**, try another network, run `curl` to see exact error. |
| 403 Forbidden | Environment is reachable; check security groups (port 80) and app logic. |
| Environment Stopped | In AWS EB console: start/resume the environment. |
| Environment Terminated | Create a new EB environment and update the base URL in `APP/app.py` and docs. |

The base URL is configured in **`APP/app.py`** as `SCALEAPP_BASE_URL` (and in **`SCALEAPP/README.md`**). If you create a new environment, update that URL everywhere.

---

## Why HTTPS No Longer Works (and How to Get It Back)

### Why you could use HTTPS before but not now

- **Default Elastic Beanstalk hostnames** (like `nearby-api-env.eba-z23r7ruf.us-east-1.elasticbeanstalk.com`) do **not** get an SSL certificate from AWS. Only HTTP (port 80) is configured by default.
- So if HTTPS worked before, it was because of one of these:
  1. **Custom domain + certificate** – You had a domain (e.g. `api.yourdomain.com`) with an SSL certificate (e.g. from AWS Certificate Manager) and a load balancer listener on port 443. If the environment was recreated, the certificate was removed, or the listener was changed, HTTPS would stop working.
  2. **Environment recreated** – A new environment gets a new load balancer. Any previous HTTPS/443 configuration does not carry over unless you add it again.
  3. **Certificate expired or deleted** – An ACM (or other) certificate you used for this environment may have expired or been deleted.
  4. **Different URL** – You might have been using a custom HTTPS URL (e.g. behind CloudFront or a custom domain) that pointed to this app; the raw `https://...elasticbeanstalk.com` URL was never officially supported.

So: **HTTPS is not available by default** on `*.elasticbeanstalk.com`. It only works if you explicitly add a certificate and a 443 listener (usually with a custom domain).

### How to enable HTTPS again

1. **Use a custom domain**  
   You need a domain you control (e.g. `api.yourdomain.com`) that you point to the Elastic Beanstalk environment (CNAME to the EB URL or to the load balancer).

2. **Request an SSL certificate in AWS**  
   - **AWS Console** → **Certificate Manager (ACM)** → **Request certificate**.  
   - Choose **Request a public certificate**, add your domain (e.g. `api.yourdomain.com`), use DNS validation, and complete validation.

3. **Add HTTPS to the load balancer**  
   - In **EC2** → **Load Balancers**, open the load balancer used by **nearby-api-env**.  
   - **Listeners** → **Add listener**:  
     - Protocol/port: **HTTPS : 443**.  
     - Default action: forward to the same target group as port 80.  
     - Security policy: e.g. ELBSecurityPolicy-TLS13-1-2-2021-06 (or a compatible one).  
     - Certificate: select the ACM certificate from step 2.

4. **Open port 443 in the load balancer security group**  
   - **EC2** → **Security Groups** → select the security group attached to the load balancer.  
   - **Inbound rules** → **Edit** → **Add rule**: Type **HTTPS**, Port **443**, Source **0.0.0.0/0** (or your preferred range). Save.

5. **Use the custom domain in the app**  
   Update **`APP/app.py`** (and any docs) so `SCALEAPP_BASE_URL` uses `https://api.yourdomain.com` (or whatever domain you set up).

After this, **https://api.yourdomain.com** will work. The raw URL **https://nearby-api-env.eba-z23r7ruf.us-east-1.elasticbeanstalk.com** will still not have a valid certificate unless you request an ACM cert for that exact hostname (which is possible but less common; most people use a custom domain).
