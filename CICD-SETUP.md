# CI/CD Setup Guide (GitHub Actions)

This project uses **GitHub Actions** for:

- **CI** – Validate SCALEAPP and APP on every push and pull request.
- **CD** – Deploy SCALEAPP to AWS Elastic Beanstalk when you push to `main`.

---

## 1. Push the project to GitHub

If the project is not on GitHub yet:

1. Create a new repository on GitHub (do not add a README if you already have one).
2. From your project root (e.g. `ScalableProject/`), run:

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

   Replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub username and repository name.

---

## 2. Add GitHub Secrets (for deployment)

The deploy workflow needs AWS credentials. Add them as **repository secrets**:

1. Open your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret** and add:

   | Name                     | Value                                      |
   |--------------------------|--------------------------------------------|
   | `AWS_ACCESS_KEY_ID`      | Your AWS access key ID                     |
   | `AWS_SECRET_ACCESS_KEY`  | Your AWS secret access key                 |

### How to get AWS credentials

1. In the **AWS Console**, go to **IAM** → **Users** → your user (or create one).
2. Open **Security credentials** → **Create access key**.
3. Choose “Command Line Interface (CLI)” and create the key.
4. Copy the **Access key ID** and **Secret access key** and paste them into the GitHub secrets above.

The IAM user must have permissions to deploy to Elastic Beanstalk (e.g. `AWSElasticBeanstalkFullAccess` or a custom policy that allows EB deploy, S3, and CloudFormation as needed).

---

## 3. What the workflows do

### CI (`.github/workflows/ci.yml`)

- **Runs on:** every push and pull request to `main` or `master`.
- **Jobs:**
  - **Validate SCALEAPP** – Installs `SCALEAPP/requirements.txt` and checks that the Flask app imports.
  - **Validate APP** – Installs `APP/requirements.txt` and checks that the Flask app imports.

No secrets are required for CI.

### CD (`.github/workflows/deploy-scaleapp.yml`)

- **Runs on:** push to `main` **only when** files under `SCALEAPP/` or the workflow file changed.
- **Job:** Installs the EB CLI, configures AWS from secrets, then runs `eb deploy nearby-api-env` from the `SCALEAPP/` directory.

So: push to `main` with changes in `SCALEAPP/` → SCALEAPP is deployed to your existing Elastic Beanstalk environment `nearby-api-env`.

---

## 4. Change the branch or environment

- **Branch:** Edit both workflow files and replace `main` (or `master`) with your default branch name.
- **EB environment:** In `.github/workflows/deploy-scaleapp.yml`, change the `EB_ENVIRONMENT` env value (e.g. to your environment name).
- **Region:** Change `AWS_REGION` in the deploy workflow if your EB app is in another region.

---

## 5. Check that it works

1. Push a commit to `main`:
   ```bash
   git add .
   git commit -m "Enable CI/CD"
   git push origin main
   ```
2. On GitHub, open the **Actions** tab. You should see:
   - **CI** run (Validate SCALEAPP + Validate APP).
   - **Deploy SCALEAPP to Elastic Beanstalk** run (only if something under `SCALEAPP/` or the deploy workflow changed).
3. If deploy succeeded, your live API URL (e.g. `http://nearby-api-env.eba-....elasticbeanstalk.com`) will serve the new code.

---

## 6. Optional: deploy only on tags

If you prefer to deploy only when you tag a release (e.g. `v1.0.0`):

1. In `.github/workflows/deploy-scaleapp.yml`, change `on` to:

   ```yaml
   on:
     push:
       tags:
         - "v*"
   ```

2. Remove the `paths` filter if you want any tag to trigger deploy.
3. To deploy, run: `git tag v1.0.0 && git push origin v1.0.0`.

You can keep the current `on: push: branches: [main]` if you prefer automatic deploy on every push to `main`.
