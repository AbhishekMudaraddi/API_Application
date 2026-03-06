# CI/CD for APP (GitHub Actions)

The pipeline **tests** the APP and **deploys** it to **AWS Elastic Beanstalk** on every push to `main`/`master`. SCALEAPP is not deployed by this pipeline.

**Workflow:** `.github/workflows/pipeline.yml` (“Test and Deploy APP”)

- **Test job:** Installs deps and verifies the Flask app loads.
- **Deploy job:** Runs only after Test passes and only on **push** to `main`/`master`. Deploys the APP to the EB environment `app-env`.

---

## Next steps to deploy APP from GitHub

### 1. One-time: Create the Elastic Beanstalk app and environment for APP

The pipeline expects an EB **application** named **APP** and an **environment** named **app-env**. Create them once from your machine:

1. Install the EB CLI if needed:  
   `pip install awsebcli`
2. Configure AWS (if not already):  
   `aws configure`  
   Use the same IAM user that has Elastic Beanstalk permissions.
3. Go to the APP folder and create the environment:
   ```bash
   cd APP
   eb create app-env
   ```
   When prompted, choose the same region as your SCALEAPP (e.g. `us-east-1`) and accept defaults if you like. This creates the application **APP** and environment **app-env** in AWS.
4. Optional: check status and URL:
   ```bash
   eb status
   eb open
   ```
5. Come back to the project root (you do not need to commit any new files from this step; the repo already has `APP/.elasticbeanstalk/config.yml`).

If you prefer to create the application and environment in the **AWS Console** (Elastic Beanstalk → Create application → Create environment), name the application **APP** and the environment **app-env**, and use the same region. The repo’s `APP/.elasticbeanstalk/config.yml` should match those names.

---

### 2. Add GitHub Secrets (for deploy)

The deploy job needs AWS credentials:

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions**.
2. Add (or confirm you have):
   - **`AWS_ACCESS_KEY_ID`** – your AWS access key
   - **`AWS_SECRET_ACCESS_KEY`** – your AWS secret key  

Use an IAM user that can deploy to Elastic Beanstalk (e.g. `AWSElasticBeanstalkFullAccess` or equivalent).

---

### 3. Commit and push

Commit the new APP files and workflow changes, then push to `main`:

```bash
cd /path/to/ScalableProject
git add APP/application.py APP/.ebignore APP/.elasticbeanstalk/config.yml .github/workflows/pipeline.yml CICD-SETUP.md
git status
git commit -m "Deploy APP to EB via GitHub Actions"
git push origin main
```

---

### 4. Verify

1. Open the repo on GitHub → **Actions**.
2. You should see **Test and Deploy APP** run: **Test APP** passes, then **Deploy APP to Elastic Beanstalk** runs (only on push to `main`/`master`).
3. When deploy succeeds, open your APP URL (from `eb status` in the APP folder, or from the EB console). You should see the Nearby Places Dashboard.

---

## Changing environment name or region

- In **`.github/workflows/pipeline.yml`**, set `EB_APP_ENVIRONMENT` and `AWS_REGION` to your environment name and region.
- In **`APP/.elasticbeanstalk/config.yml`**, set `environment` under `branch-defaults.default` and `default_region` under `global` to the same values.
