# CI/CD Setup Guide (GitHub Actions)

This project uses **one GitHub Actions pipeline** (`.github/workflows/pipeline.yml`):

- **Test** – Validates SCALEAPP and APP (install deps, verify app loads).
- **Deploy** – If tests pass and the run is a push to `main`/`master`, deploys SCALEAPP to AWS Elastic Beanstalk.

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

## 3. What the pipeline does

**Single workflow:** `.github/workflows/pipeline.yml` (“Test and Deploy”)

- **Runs on:** every push and pull request to `main` or `master`.
- **Job 1 – Test:** Installs dependencies for SCALEAPP and APP and verifies both Flask apps load. No secrets required.
- **Job 2 – Deploy:** Runs only if Test succeeds **and** the event is a **push** to `main` or `master`. Configures AWS from secrets and runs `eb deploy nearby-api-env` from the `SCALEAPP/` directory.

So: push to `main` → tests run → if they pass, SCALEAPP is deployed to Elastic Beanstalk (`nearby-api-env`). On pull requests, only the Test job runs (no deploy).

---

## 4. Change the branch or environment

- **Branch:** In `.github/workflows/pipeline.yml`, update the `on.push.branches` and the `if` condition on the deploy job to use your default branch name.
- **EB environment:** In `.github/workflows/pipeline.yml`, change the `EB_ENVIRONMENT` env value (e.g. to your environment name).
- **Region:** Change `AWS_REGION` in the same file if your EB app is in another region.

---

## 5. Check that it works

1. Push a commit to `main`:
   ```bash
   git add .
   git commit -m "Enable CI/CD"
   git push origin main
   ```
2. On GitHub, open the **Actions** tab. You should see one run: **Test and Deploy**. It will show:
   - **Test** job (validate SCALEAPP and APP).
   - **Deploy to Elastic Beanstalk** job (only after Test passes, and only on push to `main`/`master`).
3. If both jobs succeed, your live API URL (e.g. `http://nearby-api-env.eba-....elasticbeanstalk.com`) will serve the new code.

---

## 6. Optional: deploy only on tags

If you prefer to deploy only when you tag a release (e.g. `v1.0.0`), in `.github/workflows/pipeline.yml` you can add `push: tags: ["v*"]` and change the deploy job’s `if` to run only on tag pushes instead of branch pushes. Otherwise, the current setup deploys on every push to `main`/`master` after tests pass.
