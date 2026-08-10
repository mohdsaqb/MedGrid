# Stage 1: build the static assets. Never run Vite's dev server in a
# container meant for deployment - it's a development tool, not a
# production server.
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# IMPORTANT, and different from the backend: Vite bakes VITE_* variables
# into the compiled JS bundle at BUILD TIME. Unlike our backend's Settings
# (read fresh from the environment every time the container starts), this
# value is frozen into static files the moment `npm run build` runs -
# changing it later means rebuilding the image, not just restarting the
# container.
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: serve the built assets with a tiny web server. Multi-stage
# build means the final image contains ONLY nginx + the compiled dist/
# folder - no node_modules, no source code, no build toolchain.
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
