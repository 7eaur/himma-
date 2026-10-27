# Himma Web — Railway release image
FROM node:22-bookworm-slim AS build

ENV NODE_ENV=production
WORKDIR /app/apps/web

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY apps/web ./
RUN npm run build

FROM node:22-bookworm-slim AS runtime

ENV NODE_ENV=production
WORKDIR /app/apps/web

COPY --from=build /app/apps/web/package.json ./package.json
COPY --from=build /app/apps/web/package-lock.json ./package-lock.json
COPY --from=build /app/apps/web/node_modules ./node_modules
COPY --from=build /app/apps/web/.next ./.next
COPY --from=build /app/apps/web/public ./public

EXPOSE 3000
CMD ["sh", "-c", "npm run start -- -p ${PORT:-3000}"]
