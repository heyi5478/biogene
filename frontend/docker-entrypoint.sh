#!/bin/sh
# Replace the build-time sentinel with the runtime VITE_API_BASE_URL value.
# Vite inlines import.meta.env.* into the bundle at build time, so to keep
# one image cross-env we bake __VITE_API_BASE_URL__ in CI and substitute
# the real URL here, before nginx starts.

set -eu

: "${VITE_API_BASE_URL:?VITE_API_BASE_URL must be set at runtime}"

# Escape sed-replacement metachars (\ & |). We use | as the separator so
# slashes in the URL don't need escaping.
escaped=$(printf '%s' "$VITE_API_BASE_URL" | sed -e 's/[\\&|]/\\&/g')

find /usr/share/nginx/html/assets -type f \( -name '*.js' -o -name '*.css' \) \
  -exec sed -i "s|__VITE_API_BASE_URL__|${escaped}|g" {} +

echo "[entrypoint] injected VITE_API_BASE_URL=${VITE_API_BASE_URL}"
