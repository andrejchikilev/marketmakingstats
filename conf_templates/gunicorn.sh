#!/bin/bash

set -e

LOG_DIR="%(DEPLOY_DIR)s/logs"
LOG_FILE="$LOG_DIR/gunicorn.log"

test -d "$LOG_DIR" || mkdir -p "$LOG_DIR"
cd "%(DEPLOY_DIR)s"

source %(ENV_PATH)s/bin/activate
source %(ENV_PATH)s/bin/postactivate
export DJANGO_SETTINGS_MODULE="%(SETTINGS_MODULE)s"

exec gunicorn --pythonpath "%(DEPLOY_DIR)s" \
    --bind "%(GUNI_HOST)s:%(GUNI_PORT)s" \
    --workers "%(GUNI_WORKERS)s" \
    --timeout "%(GUNI_TIMEOUT)s" \
    --graceful-timeout "%(GUNI_GRACEFUL_TIMEOUT)s" \
    --worker-class "sync" \
    --user "%(USER)s" \
    --group "%(GROUP)s" \
    --log-level "info" \
    --log-file "$LOG_FILE" \
    nsfwchecker.wsgi:application
