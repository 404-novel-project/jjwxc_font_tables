#!/bin/bash

set -x

gunicorn --bind 0.0.0.0:8080  --workers "${WORKERS-$(nproc)}" --timeout "${TIMEOUT:-300}" \
  --worker-class gevent --preload "jjwxc_font_tables:create_app()"