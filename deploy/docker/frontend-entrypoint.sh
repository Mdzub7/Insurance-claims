#!/bin/sh
set -e
if [ -n "$BACKEND_BASE" ]; then
  find /usr/share/nginx/html -type f -name "*.js" -exec sed -i "s#http://localhost:8001#${BACKEND_BASE%/}#g" {} +
fi
nginx -g 'daemon off;'
