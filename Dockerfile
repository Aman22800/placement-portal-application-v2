# ---------- Stage 1: build the Vue frontend ----------
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: Python backend, serving the built frontend ----------
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Overwrite the empty frontend/dist placeholder with the real build from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN mkdir -p instance static/resumes

EXPOSE 5000

CMD ["python3", "app.py"]
