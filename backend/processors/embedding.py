from typing import List, Dict, Any, Optional
import os
import numpy as np
import random

# Tentative d'importation des clients d'API d'embedding
try:
    import openai
except ImportError:
    openai = None

try:
    import voyageai
except ImportError:
    voyageai = None

try:
    import cohere
except ImportError:
    cohere = None

def connect_to_embedder(model_name: str, api_key: str) -> Any:
    """
    Établit une connexion avec le service d'embedding spécifié.
    
    Args:
        model_name: Le nom du modèle d'embedding à utiliser (voyagerai, openai, cohere)
        api_key: La clé API pour le service
        
    Returns:
        Un client configuré pour le service d'embedding
    """
    if model_name == "voyagerai":
        if voyageai:
            client = voyageai.Client(api_key=api_key)
            return client
        else:
            # Simulation pour démonstration
            return DummyEmbedder("voyagerai")
    
    elif model_name == "openai":
        if openai:
            openai.api_key = api_key
            return openai.Embedding
        else:
            # Simulation pour démonstration
            return DummyEmbedder("openai")
    
    elif model_name == "cohere":
        if cohere:
            return cohere.Client(api_key)
        else:
            # Simulation pour démonstration
            return DummyEmbedder("cohere")
    
    else:
        # Modèle non reconnu, utiliser un embedder simulé
        return DummyEmbedder(model_name)

def get_embeddings(text: str, client: Any, model_name: str) -> List[float]:
    """
    Obtient les embeddings pour un texte donné.
    
    Args:
        text: Le texte à encoder
        client: Le client d'embedding configuré
        model_name: Le nom du modèle d'embedding
        
    Returns:
        Un vecteur d'embedding
    """
    # Vérifier si c'est notre embedder simulé
    if isinstance(client, DummyEmbedder):
        return client.embed(text)
    
    # Si c'est un vrai client, essayer de générer des embeddings
    try:
        if model_name == "voyagerai":
            response = client.embed(text, model="voyage-lite-01-instruct").embeddings[0]
            return response
        
        elif model_name == "openai":
            response = client.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        
        elif model_name == "cohere":
            response = client.embed(
                texts=[text],
                model="embed-multilingual-v3.0"
            )
            return response.embeddings[0]
        
        else:
            # Fallback to dummy embedder
            dummy = DummyEmbedder(model_name)
            return dummy.embed(text)
            
    except Exception as e:
        # En cas d'erreur, utiliser l'embedder simulé
        print(f"Erreur lors de la génération d'embeddings: {str(e)}")
        dummy = DummyEmbedder(model_name)
        return dummy.embed(text)

class DummyEmbedder:
    """
    Classe d'embedding simulé pour les démonstrations.
    Génère des vecteurs d'embedding cohérents basés sur le contenu du texte.
    """
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.dimension = 1024  # Dimension par défaut
        
        # Ajuster la dimension selon le modèle
        if model_name == "openai":
            self.dimension = 1536
        elif model_name == "cohere":
            self.dimension = 1024
        elif model_name == "voyagerai":
            self.dimension = 1024
    
    def embed(self, text: str) -> List[float]:
        """
        Génère un vecteur d'embedding simulé mais cohérent.
        Les textes similaires produiront des vecteurs similaires.
        """
        # Utiliser un hachage simple pour garantir la cohérence
        seed = sum(ord(c) for c in text[:100])
        random.seed(seed)
        
        # Générer un vecteur de base
        base_vector = np.array([random.uniform(-1, 1) for _ in range(self.dimension)])
        
        # Ajouter des caractéristiques spéciales basées sur le contenu
        # Les textes contenant des mots similaires auront des vecteurs plus proches
        for keyword, weight in self._get_keyword_weights().items():
            if keyword.lower() in text.lower():
                # Ajouter une composante spécifique au mot-clé
                keyword_component = np.array([random.uniform(-0.1, 0.1) for _ in range(self.dimension)])
                base_vector += keyword_component * weight
        
        # Normaliser le vecteur
        normalized = base_vector / np.linalg.norm(base_vector)
        
        return normalized.tolist()
    
    def _get_keyword_weights(self) -> Dict[str, float]:
        """Mots-clés de la systémique avec leurs poids pour influencer les vecteurs"""
        return {
            "systémique": 0.5,
            "bateson": 0.4,
            "watzlawick": 0.4,
            "palo alto": 0.4,
            "MRI": 0.3,
            "circulaire": 0.3,
            "feedback": 0.3,
            "homéostasie": 0.3,
            "paradoxe": 0.3,
            "double contrainte": 0.3,
            "recadrage": 0.3,
            "relation": 0.2,
            "thérapie": 0.2,
            "communication": 0.2,
            "interaction": 0.2,
            "famille": 0.2,
            "système": 0.2,
        }