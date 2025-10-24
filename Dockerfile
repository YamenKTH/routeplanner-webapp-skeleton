# Dummy Dockerfile for Railway — actual build handled by docker-compose.yml
FROM alpine:3.19

WORKDIR /app

# Copy compose and related files (optional for context)
COPY . .

# Default command: use docker-compose
CMD ["sh", "-c", "docker compose up"]
