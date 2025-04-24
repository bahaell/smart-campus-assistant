# Étape 1 : Construire l'application Angular
FROM node:20 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build --prod

# Étape 2 : Configurer NGINX pour servir l'application
FROM nginx:1.25
COPY --from=build /app/dist/smart-campus-frontend /usr/share/nginx/html

# Définir une variable d'environnement par défaut
ARG ENV=prod
COPY nginx.conf /etc/nginx/nginx.conf.prod
COPY nginx.conf.local /etc/nginx/nginx.conf.local

# Copier le fichier NGINX approprié en fonction de l'environnement
RUN if [ "$ENV" = "local" ]; then \
    cp /etc/nginx/nginx.conf.local /etc/nginx/nginx.conf; \
    else \
    cp /etc/nginx/nginx.conf.prod /etc/nginx/nginx.conf; \
    fi

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
