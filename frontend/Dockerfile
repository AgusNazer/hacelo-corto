# Multi-stage build para Next.js
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar package files
COPY package.json package-lock.json* yarn.lock* ./

# Instalar dependencias
RUN npm ci --prefer-offline --no-audit

# Copiar código fuente
COPY . .

# Build de la aplicación
RUN npm run build

# Stage final
FROM node:20-alpine

WORKDIR /app

# Instalar dumb-init para manejar signals correctamente
RUN apk add --no-cache dumb-init

# Copiar dependencias instaladas
COPY --from=builder /app/node_modules ./node_modules

# Copiar archivos necesarios para ejecutar
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Crear usuario no-root
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

USER nextjs

# Exponer puerto
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# Comando de inicio
CMD ["dumb-init", "node_modules/next/dist/bin/next", "start", "-p", "3000"]
