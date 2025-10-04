FROM node:20-alpine

WORKDIR /app/stub-node

COPY stub-node/package*.json ./ 
RUN npm install

COPY proto ./proto
COPY stub-node ./


EXPOSE 8080

CMD ["node", "server.js"]
