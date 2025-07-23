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

# Stage 2: Serve the built application with Nginx (a lightweight web server)
FROM nginx:alpine

# Copy the built assets from the 'build' stage to Nginx's public directory
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80, which Nginx will listen on
EXPOSE 80

# Command to start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]