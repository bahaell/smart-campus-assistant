# Étape 1 : Build Angular
FROM node:20 AS build

WORKDIR /app

# Copie des fichiers package pour l'installation des dépendances
COPY package.json package-lock.json ./

# Mise à jour de npm + configuration proxy (si nécessaire)
# ⚠️ Ne définis les proxies que si tu les utilises, sinon ça peut casser le build
RUN npm install -g npm@11.3.0 && \
    npm install --fetch-timeout=600000

# Copie du reste du projet
COPY . .

# Build de l'app Angular
RUN npm run build --configuration=production

# Étape 2 : Serveur NGINX
FROM nginx:1.25

# Copie des fichiers Angular buildés vers nginx
COPY --from=build /app/dist/frontend /usr/share/nginx/html

# Copie du fichier nginx personnalisé (doit exister dans ton projet)
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;", "-c", "/etc/nginx/nginx.conf"]
