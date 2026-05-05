FROM node:20-alpine AS build

# Build arguments for environment variables
ARG VITE_API_BASE
ARG VITE_GO2RTC_BASE

# Set environment variables during build
ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_GO2RTC_BASE=$VITE_GO2RTC_BASE

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# Production stage using Nginx
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
