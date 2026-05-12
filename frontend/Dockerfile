# syntax=docker/dockerfile:1.7
#
# Build the Vite SPA with Bun, serve the static bundle with nginx.
#
# Vite hard-codes `import.meta.env.VITE_API_BASE_URL` into the bundle at
# build time, but we want one image that runs in stage AND prod with
# different gateway URLs. Trick: build with a sentinel string, then have
# the runtime entrypoint sed-replace it on container start.
#
# Build (from repo root):
#     docker build -t my-project-frontend frontend/
# Run:
#     docker run --rm -p 80:80 \
#         -e VITE_API_BASE_URL=https://api.stage.example.com \
#         my-project-frontend

# ───────── Stage 1: build dist/ with Bun ─────────
FROM oven/bun:1.2-alpine AS builder

WORKDIR /build

# Manifest + lockfile alone, so layer cache survives source-only edits.
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

# Sentinel that survives Vite's minifier; entrypoint replaces it at runtime.
ENV VITE_API_BASE_URL=__VITE_API_BASE_URL__

RUN bun run build

# ───────── Stage 2: nginx serves the static bundle ─────────
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /build/dist /usr/share/nginx/html

# nginx image auto-runs every *.sh under /docker-entrypoint.d/ before
# exec'ing nginx — drop the sed-injection script in there.
COPY docker-entrypoint.sh /docker-entrypoint.d/40-inject-runtime-env.sh
RUN chmod +x /docker-entrypoint.d/40-inject-runtime-env.sh

EXPOSE 80
