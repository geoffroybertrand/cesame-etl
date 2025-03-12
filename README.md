# Document Processor pour Systémique

Une application web permettant de traiter des documents textuels, les découper en chunks cohérents, extraire des métadonnées et les indexer dans une base de données vectorielle Weaviate pour faciliter la recherche sémantique.

## Fonctionnalités

- Téléchargement et traitement de documents (PDF, DOCX, TXT)
- Découpage automatique des documents en chunks selon différentes stratégies :
  - Découpage sémantique (respects des frontières naturelles du texte)
  - Découpage par paragraphes
  - Découpage par taille fixe
- Paramétrage précis du chunking :
  - Taille des chunks
  - Chevauchement entre chunks
  - Respect des frontières du texte
- Extraction de métadonnées :
  - Langue
  - Concepts clés
  - Auteurs
  - Structure (sections)
- Visualisation et prévisualisation des chunks
- Connexion à différents services d'embeddings (VoyageAI, OpenAI, Cohere)
- Indexation dans Weaviate pour la recherche vectorielle
- Interface utilisateur intuitive et réactive

## Prérequis

- Docker et Docker Compose
- Une clé API pour un service d'embeddings (optionnel)
- Un cluster Weaviate (optionnel)

## Installation et déploiement

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/document-processor.git
cd document-processor
```

### 2. Configuration

Vous pouvez configurer l'application en modifiant les variables d'environnement dans le fichier `docker-compose.yml`.

Pour utiliser votre propre instance Weaviate ou configurer un service d'embeddings, modifiez les variables suivantes :

```yaml
environment:
  - WEAVIATE_URL=https://your-cluster.weaviate.network
  - WEAVIATE_API_KEY=your-weaviate-api-key
  - EMBEDDER_API_KEY=your-embedding-api-key
  - EMBEDDER_MODEL=voyagerai
```

### 3. Démarrer l'application

```bash
docker-compose up -d
```

L'application sera accessible à l'adresse http://localhost:3000

### 4. Arrêter l'application

```bash
docker-compose down
```

## Utilisation

### Téléchargement de documents

1. Accédez à l'interface web (http://localhost:3000)
2. Cliquez sur "Sélectionner des fichiers" ou glissez-déposez vos documents
3. Les documents téléchargés apparaîtront dans la liste à gauche

### Configuration du chunking

1. Sélectionnez un document dans la liste
2. Passez à l'onglet "Prévisualisation"
3. Ajustez les paramètres à gauche :
   - Taille des chunks
   - Chevauchement
   - Stratégie de chunking
   - Option "Respecter les frontières"
4. Cliquez sur "Appliquer les changements" pour retraiter le document

### Connexion aux services externes

1. Cliquez sur l'icône ⚙️ (Paramètres) en haut à droite
2. Configurez les services d'embeddings et Weaviate :
   - URL du cluster Weaviate
   - Clé API Weaviate
   - Modèle d'embeddings
   - Clé API pour le service d'embeddings
3. Cliquez sur les boutons "Connecter" respectifs

### Indexation dans Weaviate

1. Sélectionnez un document traité
2. Cliquez sur le bouton "Envoyer à Weaviate" en haut à droite
3. Le document sera indexé dans Weaviate et pourra être utilisé pour la recherche vectorielle

## Développement

### Structure du projet

```
document-processor/
├── docker-compose.yml        # Configuration des services Docker
├── frontend/                 # Application React
│   ├── Dockerfile            # Configuration Docker pour le frontend
│   ├── package.json          # Dépendances npm
│   ├── public/               # Fichiers statiques
│   └── src/                  # Code source React
│       ├── components/       # Composants React
│       ├── services/         # Services pour API, fichiers, etc.
│       ├── App.js            # Composant principal
│       └── index.js          # Point d'entrée
├── backend/                  # API Python
│   ├── Dockerfile            # Configuration Docker pour le backend
│   ├── requirements.txt      # Dépendances Python
│   ├── app.py                # Point d'entrée de l'API
│   └── processors/           # Modules de traitement
│       ├── chunking.py       # Logique de chunking
│       ├── embedding.py      # Intégration avec les services d'embedding
│       └── weaviate_client.py # Client Weaviate
└── README.md                 # Documentation
```

### Développement local sans Docker

**Backend**

```bash
cd backend
pip install -r requirements.txt
python app.py
```

**Frontend**

```bash
cd frontend
npm install
npm start
```

## Extensions et améliorations possibles

- Ajout d'un onglet de recherche pour interroger Weaviate
- Support de formats additionnels (HTML, ePub, etc.)
- Extraction améliorée des métadonnées avec des modèles NLP
- Chunking sémantique avec des modèles d'IA plus avancés
- Interface de requêtes sur les documents indexés
- Intégration avec des LLMs pour l'analyse et la génération de contenu
- Extraction d'images et de tableaux des documents

## Technologies utilisées

- **Frontend** : React, TypeScript, Tailwind CSS, Lucide React
- **Backend** : FastAPI, PyPDF2, python-docx
- **Base de données vectorielle** : Weaviate
- **Services d'embeddings** : VoyageAI, OpenAI, Cohere

## Licence

MIT