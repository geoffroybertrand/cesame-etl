FROM node:18-alpine

WORKDIR /app

# Créer le dossier public explicitement
RUN mkdir -p public src/components src/services

# Copier les fichiers de configuration
COPY package.json package-lock.json* tailwind.config.js postcss.config.js ./
RUN npm install

# Copier le dossier public
COPY public/ ./public/

# Copier le code source
COPY src/ ./src/

# Exposer le port
EXPOSE 3000

# Commande de démarrage
CMD ["npm", "start"]