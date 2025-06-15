# Dockerfile pour builder uniquement le front
FROM node:22

WORKDIR /frontend
COPY ../frontend/ ./

RUN npm install
RUN npm run build
