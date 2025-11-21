# Stage 1: Build the app
FROM node:18-alpine AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache.
COPY package*.json ./

# Install dependencies, forcing a clean install to prevent issues
RUN npm install

# Copy the rest of the app files
COPY . .

# Build the app for production
RUN npm run build

# Stage 2: Use nginx to serve the build
FROM nginx:alpine

# Remove the default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy the build output from the builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port for the app
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

