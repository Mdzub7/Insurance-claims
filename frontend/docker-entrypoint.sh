#!/bin/bash
# =============================================================================
# Frontend Docker Entrypoint Script
# Performs runtime configuration by replacing API URLs in JavaScript files
# =============================================================================

set -e

# Default backend URL if not provided
BACKEND_URL="${BACKEND_URL:-http://localhost:8001}"

echo "=============================================="
echo "Insurance Claims Portal - Frontend Container"
echo "=============================================="
echo "Backend API URL: ${BACKEND_URL}"
echo "=============================================="

# Directory containing JavaScript files
JS_DIR="/usr/share/nginx/html/js"

# Replace hardcoded localhost API URLs with the configured backend URL
# This handles both API_URL and API_BASE patterns

echo "Configuring API endpoints..."

# Process all JavaScript files in the js directory
for js_file in "$JS_DIR"/*.js; do
    if [ -f "$js_file" ]; then
        filename=$(basename "$js_file")
        echo "  -> Processing: $filename"
        
        # Replace various hardcoded patterns
        # Pattern 1: const API_URL = "http://localhost:8001/api/v1/claims";
        # Pattern 2: const API_BASE = "http://localhost:8001/api/v1";
        sed -i "s|http://localhost:8001|${BACKEND_URL}|g" "$js_file"
        
        # Also handle 127.0.0.1 variations
        sed -i "s|http://127.0.0.1:8001|${BACKEND_URL}|g" "$js_file"
    fi
done

# Also check for any HTML files that might have inline scripts with API URLs
echo "Checking HTML files for inline API configurations..."
for html_file in /usr/share/nginx/html/*.html /usr/share/nginx/html/**/*.html 2>/dev/null; do
    if [ -f "$html_file" ]; then
        if grep -q "localhost:8001\|127.0.0.1:8001" "$html_file" 2>/dev/null; then
            filename=$(basename "$html_file")
            echo "  -> Processing: $filename"
            sed -i "s|http://localhost:8001|${BACKEND_URL}|g" "$html_file"
            sed -i "s|http://127.0.0.1:8001|${BACKEND_URL}|g" "$html_file"
        fi
    fi
done

echo "=============================================="
echo "Configuration complete. Starting nginx..."
echo "=============================================="

# Execute the CMD (nginx)
exec "$@"

