# Vite + React frontend served via nginx.
FROM node:20-alpine AS builder

WORKDIR /app

# Declare build-time env vars — Vite bakes VITE_* into the static bundle
ARG VITE_VECINITA_MODEL_API_URL
ARG VITE_DM_API_BASE_URL
ARG VITE_VECINITA_EMBEDDING_API_URL
ENV VITE_VECINITA_MODEL_API_URL=$VITE_VECINITA_MODEL_API_URL
ENV VITE_DM_API_BASE_URL=$VITE_DM_API_BASE_URL
ENV VITE_VECINITA_EMBEDDING_API_URL=$VITE_VECINITA_EMBEDDING_API_URL

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine AS runner

COPY --from=builder /app/dist /usr/share/nginx/html

# Write minimal nginx config: port 3000 + SPA fallback so React Router deep-links work
RUN printf 'server {\n    listen 3000;\n    listen [::]:3000;\n    root /usr/share/nginx/html;\n    index index.html;\n    location / {\n        try_files $uri $uri/ /index.html;\n    }\n}\n' \
    > /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
