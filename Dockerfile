FROM node:22-alpine AS build-env
WORKDIR /app/frontend
COPY frontend/ .
RUN npm install && npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt entry.py ./
COPY backend/ ./backend
COPY --from=build-env /app/frontend/dist ./frontend/dist
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgobject-2.0-0 libnspr4 libnss3 libnssutil3 libdbus-1-3 libgio2.0-0 libatk1.0-0 libatk-bridge2.0-0 libexpat1 libatspi2.0-0 libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 libxcb1 libxkbcommon0 libasound2 && pip install --no-cache-dir -r requirements.txt && playwright install chromium 
EXPOSE 8000
CMD ["python","entry.py"]

