# Frontend — build dengan Vite, serve dengan nginx + proxy API
FROM node:20-alpine AS build
WORKDIR /app

# deps dulu (layer cache)
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# source + build (VITE_API_BASE kosong di production → URL relatif same-origin)
COPY . .
ENV VITE_API_BASE=""
RUN npm run build

# ---- runtime ----
FROM nginx:1.27-alpine
ENV TZ=Asia/Jakarta
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
