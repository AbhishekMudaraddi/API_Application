#!/usr/bin/env bash
set -euo pipefail

# EB helper script for APP only.
# - Deploys/terminates the APP Elastic Beanstalk environment (app-env)
# - Does NOT touch SCALEAPP (nearby-api-env)

ACTION="${1:-}"

APP_DIR="APP"
APP_ENV="app-env"

usage() {
  cat <<'EOF'
Usage:
  ./eb_app_tools.sh deploy
  ./eb_app_tools.sh terminate
  ./eb_app_tools.sh status

Notes:
  - This script ONLY manages the APP environment: app-env
  - It will NOT deploy/terminate SCALEAPP (nearby-api-env)
  - Team safety rule: do NOT run 'eb create' unless app-env is truly missing.
  - Normal operations should use only:
      ./eb_app_tools.sh deploy
      ./eb_app_tools.sh status
      ./eb_app_tools.sh terminate
  - Requires EB CLI installed: pip install awsebcli
  - Requires AWS credentials configured for EB
EOF
}

require_eb() {
  if ! command -v eb >/dev/null 2>&1; then
    echo "Error: 'eb' CLI not found. Install with: pip install awsebcli" >&2
    exit 1
  fi
}

require_app_dir() {
  if [[ ! -d "$APP_DIR" ]]; then
    echo "Error: APP directory not found at '$APP_DIR'." >&2
    exit 1
  fi
  if [[ ! -f "$APP_DIR/.elasticbeanstalk/config.yml" ]]; then
    echo "Error: Missing EB config at '$APP_DIR/.elasticbeanstalk/config.yml'." >&2
    exit 1
  fi
}

check_app_env_exists() {
  # We intentionally check before deploy/status so accidental env recreation is avoided.
  # If AWS CLI isn't present, skip this precheck and let EB CLI handle command errors.
  if ! command -v aws >/dev/null 2>&1; then
    return 0
  fi

  local env_status
  env_status="$(aws elasticbeanstalk describe-environments \
    --region us-east-1 \
    --environment-names "$APP_ENV" \
    --query "Environments[0].Status" \
    --output text 2>/dev/null || true)"

  if [[ -z "$env_status" || "$env_status" == "None" || "$env_status" == "Terminated" ]]; then
    echo "Error: APP environment '$APP_ENV' is missing or terminated." >&2
    echo "Rule: do NOT run 'eb create' unless this env is truly missing." >&2
    echo "If needed, recreate once manually, then continue using this script only." >&2
    exit 1
  fi
}

do_deploy() {
  echo "==> Deploying APP to Elastic Beanstalk env: $APP_ENV"
  ( cd "$APP_DIR" && eb deploy "$APP_ENV" )
}

do_status() {
  echo "==> APP Elastic Beanstalk status: $APP_ENV"
  ( cd "$APP_DIR" && eb status "$APP_ENV" )
}

do_terminate() {
  echo "==> Terminating APP Elastic Beanstalk env: $APP_ENV"
  echo "    This will stop APP resources and may take a few minutes."
  ( cd "$APP_DIR" && eb terminate "$APP_ENV" --force )
}

case "$ACTION" in
  deploy)
    require_eb
    require_app_dir
    check_app_env_exists
    do_deploy
    ;;
  status)
    require_eb
    require_app_dir
    check_app_env_exists
    do_status
    ;;
  terminate)
    require_eb
    require_app_dir
    do_terminate
    ;;
  *)
    usage
    exit 1
    ;;
esac



# ./eb_app_tools.sh status
# ./eb_app_tools.sh deploy
# ./eb_app_tools.sh terminate