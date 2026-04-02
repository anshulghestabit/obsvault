FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY public/ ./public/
COPY src/ ./src/
COPY README.md ./README.md

EXPOSE 4000

CMD ["npm", "start"]
