FROM node:20-alpine
WORKDIR /app

# Instala sqlite3 dependencies if needed for sqlite3 package
RUN apk add --no-cache python3 make g++ 

COPY package*.json ./
RUN npm ci --legacy-peer-deps

COPY . .

# Run typescript build or ts-node (assume ts-node since there's no dist in migrations usually, but let's check if it builds or runs with ts-node)
# Harness api uses ts-node for servidor-principal.ts
EXPOSE 3000

CMD ["npx", "ts-node", "servidor-principal.ts"]
