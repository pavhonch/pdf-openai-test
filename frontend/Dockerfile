FROM node:22-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY index.html vite.config.ts tsconfig.json tsconfig.node.json ./
COPY src ./src

ENV VITE_API_URL=http://localhost:8000

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
