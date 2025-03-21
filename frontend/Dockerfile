ARG BUILD_IMAGE=node
ARG BUILD_IMAGE_TAG=18-alpine
FROM ${BUILD_IMAGE}:${BUILD_IMAGE_TAG}

WORKDIR /app

ARG REACT_APP_BASE_URL=http://localhost:8000/


ENV REACT_APP_BASE_URL=$REACT_APP_BASE_URL

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build


RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]
