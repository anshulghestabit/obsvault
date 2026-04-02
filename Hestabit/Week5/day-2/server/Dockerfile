FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY server.js .
USER node

EXPOSE 5000

CMD ["node", "server.js"]