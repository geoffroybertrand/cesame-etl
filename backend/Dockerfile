FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Créer les dossiers nécessaires
RUN mkdir -p processors uploaded_files

# Copier les fichiers processors
COPY processors/__init__.py processors/
COPY processors/chunking.py processors/
COPY processors/document_extractor.py processors/
COPY processors/embedding.py processors/

# Copier le code principal
COPY app.py .

# Créer un fichier .env pour les variables d'environnement
RUN echo "PYTHONPATH=/app" > .env

# Exposer le port
EXPOSE 8000

# Commande de démarrage avec le PYTHONPATH spécifié
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]