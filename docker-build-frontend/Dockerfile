# Dockerfile pour builder uniquement le front
FROM node:22

WORKDIR /frontend
COPY ../frontend/package.json ./
RUN npm install

COPY ../frontend/ ./
RUN npm run build
