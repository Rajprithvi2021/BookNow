FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY src src
COPY public public
COPY next.config.js .
COPY tailwind.config.js .
COPY tsconfig.json .
COPY postcss.config.js .

# Build application
RUN npm run build

# Expose port
EXPOSE 3000

# Start server
CMD ["npm", "start"]
