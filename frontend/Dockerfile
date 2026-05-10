# Frontend Dockerfile - Angular with SSR
FROM node:18-alpine AS builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend code
COPY frontend . 

# Build for production with SSR
RUN npm run build:ssr

# Production stage
FROM node:18-alpine

WORKDIR /app/frontend

# Copy built application from builder
COPY --from=builder /app/frontend/dist ./dist
COPY --from=builder /app/frontend/node_modules ./node_modules
COPY --from=builder /app/frontend/package*.json ./

# Expose port
EXPOSE 4200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:4200 || exit 1

# Run SSR server
CMD ["npm", "run", "serve:ssr"]
