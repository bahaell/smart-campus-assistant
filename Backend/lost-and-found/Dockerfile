# Utilise une image officielle Python basée sur Debian Bullseye
FROM python:3.10-slim-bullseye

# Installe les dépendances système nécessaires pour OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier seulement requirements.txt pour installation rapide
COPY requirements.txt .

# Mise à jour de pip et installation des dépendances Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copier le reste de l'application
COPY . .

# Expose le port utilisé par l'application
EXPOSE 8002

# Commande pour démarrer l'application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
