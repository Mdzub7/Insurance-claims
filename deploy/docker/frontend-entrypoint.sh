#!/bin/sh
set -e
find /usr/share/nginx/html -type f -name "*.js" -exec sed -i "s#http://localhost:8001#${BACKEND_BASE%/}#g" {} +
nginx -g 'daemon off;'
