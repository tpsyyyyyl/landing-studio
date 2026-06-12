# Stage 1: build React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8080
CMD ["./start.sh"]
