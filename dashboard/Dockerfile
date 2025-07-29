# Stage 1: Build the React application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
# This ensures that npm install isn't re-run unless dependencies change
COPY package*.json ./
RUN npm install

# Copy the rest of your application code
COPY . .

# Build the Vite application for production
RUN npm run build

# Stage 2: Serve the built application with Caddy
FROM caddy:latest

# Copy the built assets from the 'build' stage to Caddy's public directory
COPY --from=build /app/dist /srv

# Copy Caddyfile for configuration
COPY conf/Caddyfile /etc/caddy/Caddyfile

# Expose ports 80 (HTTP) and 443 (HTTPS)
EXPOSE 80 443

# Caddy will automatically start with the Caddyfile
