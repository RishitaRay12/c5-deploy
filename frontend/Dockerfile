FROM node:18-alpine

WORKDIR /app

# Copy dependency definitions
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./

# Install all dependencies (including devDependencies needed for npm run dev)
RUN \
  if [ -f yarn.lock ]; then yarn install; \
  elif [ -f package-lock.json ]; then npm install; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm install; \
  else npm install; \
  fi

# Copy rest of the application code
COPY . .

# Set host to 0.0.0.0 so the server listens externally from inside the container
ENV HOST=0.0.0.0

EXPOSE 5173

# Run the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
