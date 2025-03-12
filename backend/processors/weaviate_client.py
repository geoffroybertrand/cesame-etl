import os
import json
import weaviate
from typing import Dict, List, Any, Optional, Union
import logging

# Configurer le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeaviateClient:
    """
    Client pour interagir avec Weaviate.
    Cette classe encapsule toutes les interactions avec la base de données vectorielle.
    """
    
    def __init__(self, url: str = None, api_key: str = None):
        """
        Initialise le client Weaviate.
        
        Args:
            url: L'URL du cluster Weaviate
            api_key: La clé API pour l'authentification
        """
        self.url = url or os.environ.get("WEAVIATE_URL", "")
        self.api_key = api_key or os.environ.get("WEAVIATE_API_KEY", "")
        self.client = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Établit une connexion avec Weaviate.
        
        Returns:
            True si la connexion est réussie, False sinon
        """
        try:
            # Configurer l'authentification si une clé API est fournie
            auth_config = None
            if self.api_key:
                auth_config = weaviate.auth.AuthApiKey(api_key=self.api_key)
            
            # Créer le client
            self.client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config
            )
            
            # Vérifier la connexion
            meta = self.client.get_meta()
            logger.info(f"Connected to Weaviate version: {meta['version']}")
            
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            self.connected = False
            return False
    
    def check_connection(self) -> bool:
        """
        Vérifie si le client est connecté.
        
        Returns:
            True si connecté, False sinon
        """
        if not self.connected or not self.client:
            return False
        
        try:
            self.client.get_meta()
            return True
        except:
            self.connected = False
            return False
    
    def create_class(self, class_name: str, class_description: str = "", vectorizer: str = "none") -> bool:
        """
        Crée une classe dans Weaviate si elle n'existe pas déjà.
        
        Args:
            class_name: Le nom de la classe à créer
            class_description: La description de la classe
            vectorizer: Le vectoriseur à utiliser (none, text2vec-contextionary, etc.)
            
        Returns:
            True si la classe est créée ou existe déjà, False en cas d'erreur
        """
        if not self.check_connection():
            return False
        
        try:
            # Vérifier si la classe existe déjà
            schema = self.client.schema.get()
            class_names = [c["class"] for c in schema["classes"]] if "classes" in schema else []
            
            if class_name in class_names:
                logger.info(f"Class {class_name} already exists")
                return True
            
            # Créer la classe
            class_obj = {
                "class": class_name,
                "description": class_description,
                "vectorizer": vectorizer
            }
            
            self.client.schema.create_class(class_obj)
            logger.info(f"Created class {class_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create class {class_name}: {str(e)}")
            return False
    
    def create_document_chunk_class(self) -> bool:
        """
        Crée la classe DocumentChunk dans Weaviate.
        
        Returns:
            True si la classe est créée avec succès, False sinon
        """
        properties = [
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Le contenu textuel du chunk"
            },
            {
                "name": "documentId",
                "dataType": ["string"],
                "description": "L'identifiant du document parent"
            },
            {
                "name": "position",
                "dataType": ["string"],
                "description": "La position du chunk dans le document"
            },
            {
                "name": "pageRange",
                "dataType": ["string"],
                "description": "La plage de pages couverte par le chunk"
            },
            {
                "name": "section",
                "dataType": ["string"],
                "description": "La section du document"
            },
            {
                "name": "keyConcepts",
                "dataType": ["string[]"],
                "description": "Les concepts clés identifiés dans le chunk"
            }
        ]
        
        return self.create_class_with_properties("DocumentChunk", "Un chunk de document avec son contenu et ses métadonnées", properties)
    
    def create_indexing_stats_class(self) -> bool:
        """
        Crée la classe IndexingStats dans Weaviate.
        
        Returns:
            True si la classe est créée avec succès, False sinon
        """
        properties = [
            {
                "name": "documentId",
                "dataType": ["string"],
                "description": "L'identifiant du document"
            },
            {
                "name": "chunksCount",
                "dataType": ["int"],
                "description": "Nombre de chunks indexés"
            },
            {
                "name": "totalTokens",
                "dataType": ["int"],
                "description": "Nombre total de tokens"
            },
            {
                "name": "chunkingStrategy",
                "dataType": ["string"],
                "description": "Stratégie de chunking utilisée"
            },
            {
                "name": "chunkSize",
                "dataType": ["int"],
                "description": "Taille des chunks"
            },
            {
                "name": "chunkOverlap",
                "dataType": ["int"],
                "description": "Chevauchement des chunks"
            },
            {
                "name": "cleaningApplied",
                "dataType": ["boolean"],
                "description": "Si le nettoyage a été appliqué"
            },
            {
                "name": "cleanedPercentage",
                "dataType": ["number"],
                "description": "Pourcentage de texte supprimé lors du nettoyage"
            },
            {
                "name": "timestamp",
                "dataType": ["string"],
                "description": "Horodatage de l'indexation"
            }
        ]
        
        return self.create_class_with_properties("IndexingStats", "Statistiques d'indexation de documents", properties)
    
    def create_class_with_properties(self, class_name: str, class_description: str, properties: List[Dict[str, Any]]) -> bool:
        """
        Crée une classe avec des propriétés spécifiques.
        
        Args:
            class_name: Le nom de la classe
            class_description: La description de la classe
            properties: Liste des propriétés à ajouter
            
        Returns:
            True si la classe est créée avec succès, False sinon
        """
        if not self.check_connection():
            return False
        
        try:
            # Vérifier si la classe existe déjà
            schema = self.client.schema.get()
            class_names = [c["class"] for c in schema["classes"]] if "classes" in schema else []
            
            if class_name in class_names:
                logger.info(f"Class {class_name} already exists")
                return True
            
            # Créer la classe avec les propriétés
            class_obj = {
                "class": class_name,
                "description": class_description,
                "vectorizer": "none",  # Nous fournissons nos propres vecteurs
                "properties": properties
            }
            
            self.client.schema.create_class(class_obj)
            logger.info(f"Created class {class_name} with {len(properties)} properties")
            return True
        except Exception as e:
            logger.error(f"Failed to create class {class_name}: {str(e)}")
            return False
    
    def batch_import_document_chunks(self, chunks: List[Dict[str, Any]], document_id: str, 
                                     embeddings: List[List[float]]) -> bool:
        """
        Importe un lot de chunks de document dans Weaviate.
        
        Args:
            chunks: Liste des chunks à importer
            document_id: ID du document parent
            embeddings: Liste des vecteurs d'embedding correspondant aux chunks
            
        Returns:
            True si l'importation est réussie, False sinon
        """
        if not self.check_connection():
            return False
        
        if len(chunks) != len(embeddings):
            logger.error(f"Number of chunks ({len(chunks)}) does not match number of embeddings ({len(embeddings)})")
            return False
        
        try:
            # S'assurer que la classe existe
            self.create_document_chunk_class()
            
            # Importer les chunks
            with self.client.batch as batch:
                for i, chunk in enumerate(chunks):
                    # Préparer les propriétés
                    properties = {
                        "content": chunk["content"],
                        "documentId": document_id,
                        "position": chunk["position"],
                        "pageRange": chunk["metadata"]["page_range"],
                        "section": chunk["metadata"]["section"],
                        "keyConcepts": chunk["metadata"]["key_concepts"]
                    }
                    
                    # Ajouter à Weaviate avec le vecteur
                    batch.add_data_object(
                        data_object=properties,
                        class_name="DocumentChunk",
                        vector=embeddings[i]
                    )
            
            logger.info(f"Imported {len(chunks)} chunks for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to import chunks: {str(e)}")
            return False
    
    def store_indexing_stats(self, stats: Dict[str, Any]) -> bool:
        """
        Stocke les statistiques d'indexation dans Weaviate.
        
        Args:
            stats: Dictionnaire contenant les statistiques d'indexation
            
        Returns:
            True si l'opération est réussie, False sinon
        """
        if not self.check_connection():
            return False
        
        try:
            # S'assurer que la classe existe
            self.create_indexing_stats_class()
            
            # Préparer les propriétés
            properties = {
                "documentId": stats["document_id"],
                "chunksCount": stats["chunks_count"],
                "totalTokens": stats["total_tokens"],
                "chunkingStrategy": stats["chunking_strategy"],
                "chunkSize": stats["chunk_size"],
                "chunkOverlap": stats["chunk_overlap"],
                "cleaningApplied": stats["cleaning_applied"],
                "cleanedPercentage": stats["cleaned_percentage"],
                "timestamp": stats["timestamp"]
            }
            
            # Ajouter à Weaviate
            self.client.data_object.create(
                data_object=properties,
                class_name="IndexingStats"
            )
            
            logger.info(f"Stored indexing stats for document {stats['document_id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to store indexing stats: {str(e)}")
            return False
    
    def search_similar_chunks(self, query: str, embedding: List[float], limit: int = 5, 
                              filter_document_id: str = None) -> List[Dict[str, Any]]:
        """
        Recherche des chunks similaires à une requête.
        
        Args:
            query: Texte de la requête
            embedding: Vecteur d'embedding de la requête
            limit: Nombre maximum de résultats à retourner
            filter_document_id: Filtre optionnel par ID de document
            
        Returns:
            Liste des chunks similaires
        """
        if not self.check_connection():
            return []
        
        try:
            # Préparer la requête nearVector
            query_params = {
                "vector": embedding,
                "certainty": 0.7
            }
            
            # Préparer les filtres si nécessaire
            where_filter = None
            if filter_document_id:
                where_filter = {
                    "path": ["documentId"],
                    "operator": "Equal",
                    "valueString": filter_document_id
                }
            
            # Exécuter la requête
            result = self.client.query.get(
                "DocumentChunk", 
                ["content", "documentId", "position", "pageRange", "section", "keyConcepts"]
            ).with_near_vector(
                query_params
            ).with_limit(limit)
            
            if where_filter:
                result = result.with_where(where_filter)
            
            response = result.do()
            
            # Extraire les résultats
            chunks = []
            if "data" in response and "Get" in response["data"] and "DocumentChunk" in response["data"]["Get"]:
                chunks = response["data"]["Get"]["DocumentChunk"]
            
            logger.info(f"Found {len(chunks)} similar chunks")
            return chunks
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {str(e)}")
            return []
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les chunks d'un document.
        
        Args:
            document_id: ID du document
            
        Returns:
            Liste des chunks du document
        """
        if not self.check_connection():
            return []
        
        try:
            # Préparer le filtre
            where_filter = {
                "path": ["documentId"],
                "operator": "Equal",
                "valueString": document_id
            }
            
            # Exécuter la requête
            result = self.client.query.get(
                "DocumentChunk", 
                ["content", "documentId", "position", "pageRange", "section", "keyConcepts"]
            ).with_where(where_filter).do()
            
            # Extraire les résultats
            chunks = []
            if "data" in result and "Get" in result["data"] and "DocumentChunk" in result["data"]["Get"]:
                chunks = result["data"]["Get"]["DocumentChunk"]
            
            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks
        except Exception as e:
            logger.error(f"Failed to get document chunks: {str(e)}")
            return []
    
    def get_indexing_stats(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les statistiques d'indexation d'un document.
        
        Args:
            document_id: ID du document
            
        Returns:
            Dictionnaire des statistiques d'indexation ou None si non trouvé
        """
        if not self.check_connection():
            return None
        
        try:
            # Préparer le filtre
            where_filter = {
                "path": ["documentId"],
                "operator": "Equal",
                "valueString": document_id
            }
            
            # Exécuter la requête
            result = self.client.query.get(
                "IndexingStats", 
                ["documentId", "chunksCount", "totalTokens", "chunkingStrategy", 
                 "chunkSize", "chunkOverlap", "cleaningApplied", "cleanedPercentage", "timestamp"]
            ).with_where(where_filter).do()
            
            # Extraire les résultats
            stats = None
            if ("data" in result and "Get" in result["data"] and 
                "IndexingStats" in result["data"]["Get"] and 
                len(result["data"]["Get"]["IndexingStats"]) > 0):
                stats = result["data"]["Get"]["IndexingStats"][0]
            
            if stats:
                logger.info(f"Retrieved indexing stats for document {document_id}")
            else:
                logger.info(f"No indexing stats found for document {document_id}")
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get indexing stats: {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Supprime un document et tous ses chunks.
        
        Args:
            document_id: ID du document à supprimer
            
        Returns:
            True si la suppression est réussie, False sinon
        """
        if not self.check_connection():
            return False
        
        try:
            # Supprimer les chunks
            where_chunk_filter = {
                "path": ["documentId"],
                "operator": "Equal",
                "valueString": document_id
            }
            self.client.batch.delete_objects(
                class_name="DocumentChunk",
                where=where_chunk_filter
            )
            
            # Supprimer les stats
            where_stats_filter = {
                "path": ["documentId"],
                "operator": "Equal",
                "valueString": document_id
            }
            self.client.batch.delete_objects(
                class_name="IndexingStats",
                where=where_stats_filter
            )
            
            logger.info(f"Deleted document {document_id} with all its chunks and stats")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Récupère le schéma Weaviate.
        
        Returns:
            Dictionnaire contenant le schéma ou un dictionnaire vide en cas d'erreur
        """
        if not self.check_connection():
            return {}
        
        try:
            schema = self.client.schema.get()
            return schema
        except Exception as e:
            logger.error(f"Failed to get schema: {str(e)}")
            return {}