FROM node:20-alpine

WORKDIR /app/stub-node

COPY stub-node/package*.json ./ 
RUN npm install

COPY stub-node ./

RUN export GAME_BASE=http://game-server-service:50051
RUN export VALIDATION_BASE=http://validation-server-service:50052

EXPOSE 8080

CMD ["node", "server.js"]
