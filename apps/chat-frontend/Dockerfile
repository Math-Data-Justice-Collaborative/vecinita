# Frontend Dockerfile - Vecinita React Vite Application
# Multi-stage build for optimized production image

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_GATEWAY_URL=/api/v1
ARG VITE_BACKEND_URL=http://localhost:8000
ARG VITE_AGENT_REQUEST_TIMEOUT_MS=90000
ARG VITE_AGENT_STREAM_TIMEOUT_MS=120000
ARG VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS=15000
ARG VITE_DEV_ADMIN_ENABLED=false
ARG VITE_DEV_ADMIN_EMAIL=
ARG VITE_DEV_ADMIN_PASSWORD=
ARG VITE_DEV_ADMIN_TOKEN=

ENV VITE_GATEWAY_URL=$VITE_GATEWAY_URL
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
ENV VITE_AGENT_REQUEST_TIMEOUT_MS=$VITE_AGENT_REQUEST_TIMEOUT_MS
ENV VITE_AGENT_STREAM_TIMEOUT_MS=$VITE_AGENT_STREAM_TIMEOUT_MS
ENV VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS=$VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS
ENV VITE_DEV_ADMIN_ENABLED=$VITE_DEV_ADMIN_ENABLED
ENV VITE_DEV_ADMIN_EMAIL=$VITE_DEV_ADMIN_EMAIL
ENV VITE_DEV_ADMIN_PASSWORD=$VITE_DEV_ADMIN_PASSWORD
ENV VITE_DEV_ADMIN_TOKEN=$VITE_DEV_ADMIN_TOKEN

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage - serve with lightweight HTTP server
FROM node:20-alpine

WORKDIR /app

# Install a lightweight HTTP server
RUN npm install -g serve

# Copy built assets from builder
COPY --from=builder /app/dist ./dist

# Render (and other hosts) set PORT — default 10000 on Render Web Services.
# Bind all interfaces so the platform health check / proxy can reach the process.
EXPOSE 10000

# shell form so $PORT is honored at container start (do not hardcode Vite dev 5173)
CMD ["sh", "-c", "exec serve -s dist --no-port-switching -l tcp://0.0.0.0:${PORT:-10000}"]
