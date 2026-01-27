FROM node:18-alpine AS build

WORKDIR /app

COPY package.json yarn.lock .yarnrc.yml .yarn/ ./
RUN corepack enable && yarn install --immutable

COPY . .

ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN yarn build

FROM nginx:1.25-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
