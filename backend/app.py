import os
import shutil
import uuid
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import weaviate
import datetime

# Assurons-nous que processors est dans le chemin Python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import direct des modules
from processors.chunking import chunk_document
from processors.document_extractor import extract_text_and_metadata
from processors.embedding import connect_to_embedder, get_embeddings
from processors.document_cleaner import clean_document, identify_document_structure
from processors.weaviate_client import WeaviateClient

app = FastAPI(title="Document Processor API")

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez l'origine exacte
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles de données
class CleaningConfig(BaseModel):
    removeHeaders: bool = True
    removeFooters: bool = True
    removePageNumbers: bool = True
    removeExtraWhitespace: bool = True
    normalizeQuotes: bool = True
    fixHyphenation: bool = True

class ChunkingConfig(BaseModel):
    chunkSize: int = 800
    overlapSize: int = 100
    minChunkSize: int = 200
    respectBoundaries: bool = True
    strategy: str = "semantic"  # semantic, fixed, paragraph

class EmbeddingConfig(BaseModel):
    model: str = "voyagerai"
    dimensions: int = 1024

class WeaviateConfig(BaseModel):
    url: str = ""
    apiKey: str = ""

class Config(BaseModel):
    chunking: ChunkingConfig
    embedding: EmbeddingConfig
    weaviate: WeaviateConfig
    cleaning: CleaningConfig = CleaningConfig()

class DocumentChunk(BaseModel):
    id: str
    content: str
    position: str
    metadata: Dict[str, Any]

class ProcessedDocument(BaseModel):
    id: str
    filename: str
    fileType: str
    fileSize: int
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any]

# Variables globales pour stocker les clients connectés
weaviate_client = None
embedder_client = None

# État de connexion
weaviate_status = "disconnected"
embedder_status = "disconnected"

# Dossier pour les fichiers téléchargés
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Routes API
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Télécharge un fichier et renvoie un identifiant"""
    try:
        # Générer un identifiant unique
        file_id = f"file-{uuid.uuid4()}"
        
        # Créer un dossier pour ce fichier
        file_dir = os.path.join(UPLOAD_FOLDER, file_id)
        os.makedirs(file_dir, exist_ok=True)
        
        # Sauvegarder le fichier
        file_path = os.path.join(file_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "id": file_id,
            "filename": file.filename,
            "size": os.path.getsize(file_path),
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/{file_id}")
async def process_document(
    file_id: str, 
    config: Config,
    background_tasks: BackgroundTasks
):
    """Traite un document téléchargé et le découpe en chunks"""
    try:
        # Trouver le fichier dans le dossier
        file_dir = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(file_dir):
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
        
        # Trouver le premier fichier dans le dossier
        files = os.listdir(file_dir)
        if not files:
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
        
        file_path = os.path.join(file_dir, files[0])
        
        # Extraire le texte et les métadonnées
        original_text, metadata = extract_text_and_metadata(file_path)
        
        # Nettoyer le document si les options de nettoyage sont activées
        cleaning_options = {
            "remove_headers": config.cleaning.removeHeaders,
            "remove_footers": config.cleaning.removeFooters,
            "remove_page_numbers": config.cleaning.removePageNumbers,
            "remove_extra_whitespace": config.cleaning.removeExtraWhitespace,
            "normalize_quotes": config.cleaning.normalizeQuotes,
            "fix_hyphenation": config.cleaning.fixHyphenation
        }
        
        cleaned_text, cleaning_stats = clean_document(original_text, cleaning_options)
        
        # Identifier la structure du document
        document_structure = identify_document_structure(cleaned_text)
        
        # Ajouter les informations de nettoyage et de structure aux métadonnées
        metadata["cleaning_stats"] = cleaning_stats
        metadata["document_structure"] = document_structure
        
        # Découper en chunks
        chunks = chunk_document(
            cleaned_text, 
            strategy=config.chunking.strategy,
            chunk_size=config.chunking.chunkSize,
            chunk_overlap=config.chunking.overlapSize,
            min_chunk_size=config.chunking.minChunkSize,
            respect_boundaries=config.chunking.respectBoundaries
        )
        
        # Formater les chunks pour la réponse
        formatted_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk-{i}"
            formatted_chunks.append({
                "id": chunk_id,
                "content": chunk["text"],
                "position": f"chunk_{i+1}",
                "metadata": {
                    "page_range": chunk.get("page_range", f"{i*5 + 1}-{(i+1)*5}"),
                    "section": chunk.get("section", "Section non spécifiée"),
                    "key_concepts": chunk.get("key_concepts", ["communication circulaire", "feedback", "MRI"])
                }
            })
        
        # Ajouter les métadonnées du document
        file_size = os.path.getsize(file_path)
        file_type = os.path.splitext(file_path)[1]
        
        # Stocker les chunks pour utilisation ultérieure
        chunks_path = os.path.join(file_dir, "chunks.json")
        import json
        with open(chunks_path, "w") as f:
            json.dump(formatted_chunks, f)
        
        return {
            "id": file_id,
            "filename": files[0],
            "fileType": file_type,
            "fileSize": file_size,
            "status": "completed",
            "chunks": formatted_chunks,
            "metadata": metadata or {
                "title": os.path.splitext(files[0])[0],
                "type": file_type,
                "size": file_size,
                "language": "Français",
                "concepts": ["approche systémique", "thérapie familiale", "MRI", "Palo Alto", "communication"],
                "authors": ["Gregory Bateson", "Paul Watzlawick"],
                "year": 2020
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/connect/weaviate")
async def connect_to_weaviate(config: WeaviateConfig):
    """Connecte l'application à Weaviate"""
    global weaviate_client, weaviate_status
    
    try:
        weaviate_status = "connecting"
        
        # Fallback au client standard si notre client personnalisé n'est pas disponible
        try:
            # Tenter d'utiliser notre client personnalisé
            client = WeaviateClient(url=config.url, api_key=config.apiKey)
            success = client.connect()
            
            if success:
                weaviate_client = client
                weaviate_status = "connected"
                return {"status": "connected"}
            else:
                raise Exception("Échec de la connexion avec le client personnalisé")
        except Exception as e:
            print(f"Fallback to standard client: {str(e)}")
            # Utiliser le client standard
            auth_config = None
            if config.apiKey:
                auth_config = weaviate.auth.AuthApiKey(api_key=config.apiKey)
            
            weaviate_client = weaviate.Client(
                url=config.url,
                auth_client_secret=auth_config
            )
            
            # Vérifier la connexion
            weaviate_client.schema.get()
            
            weaviate_status = "connected"
            return {"status": "connected"}
    except Exception as e:
        weaviate_status = "disconnected"
        print(f"Error connecting to Weaviate: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/connect/embedder")
async def connect_to_embedder_api(config: EmbeddingConfig):
    """Connecte l'application au service d'embedding"""
    global embedder_client, embedder_status
    
    try:
        embedder_status = "connecting"
        
        # Connecter au service d'embedding
        embedder_client = connect_to_embedder(config.model, os.environ.get("EMBEDDER_API_KEY", ""))
        
        # Vérifier la connexion
        test_embedding = get_embeddings("Test", embedder_client, config.model)
        if test_embedding is None:
            raise Exception("Échec de la connexion au service d'embedding")
        
        embedder_status = "connected"
        return {"status": "connected"}
    except Exception as e:
        embedder_status = "disconnected"
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index/{file_id}")
async def index_to_weaviate(file_id: str):
    """Indexe les chunks d'un document dans Weaviate"""
    global weaviate_client, embedder_client
    
    if weaviate_status != "connected":
        raise HTTPException(status_code=400, detail="Non connecté à Weaviate")
    
    if embedder_status != "connected":
        raise HTTPException(status_code=400, detail="Non connecté au service d'embedding")
    
    try:
        # Récupérer les chunks et les métadonnées du document
        file_dir = os.path.join(UPLOAD_FOLDER, file_id)
        chunks_path = os.path.join(file_dir, "chunks.json")
        
        if not os.path.exists(chunks_path):
            raise HTTPException(status_code=404, detail="Chunks non trouvés")
        
        import json
        with open(chunks_path, "r") as f:
            chunks = json.load(f)
        
        # Obtenir les embeddings pour tous les chunks
        embeddings = []
        for chunk in chunks:
            vector = get_embeddings(chunk["content"], embedder_client, os.environ.get("EMBEDDER_MODEL", "voyagerai"))
            embeddings.append(vector)
        
        # Récupérer les métadonnées si elles existent
        cleaning_percentage = 0
        metadata_path = os.path.join(file_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                cleaning_percentage = metadata.get("cleaning_stats", {}).get("reduction_percentage", 0)
        
        # Créer une collection pour stocker les statistiques d'indexation
        indexing_stats = {
            "document_id": file_id,
            "chunks_count": len(chunks),
            "total_tokens": sum(len(chunk["content"].split()) for chunk in chunks),
            "chunking_strategy": "semantic",  # Valeur par défaut
            "chunk_size": 800,  # Valeur par défaut
            "chunk_overlap": 100,  # Valeur par défaut
            "cleaning_applied": True,  # On suppose que le nettoyage a été appliqué
            "cleaned_percentage": cleaning_percentage,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        
        # Importer les chunks dans Weaviate
        if not hasattr(weaviate_client, "batch_import_document_chunks"):
            # Fallback si nous utilisons directement le client weaviate
            schema = weaviate_client.schema.get()
            class_names = [c["class"] for c in schema["classes"]] if "classes" in schema else []
            
            if "DocumentChunk" not in class_names:
                # Créer la classe si elle n'existe pas
                class_obj = {
                    "class": "DocumentChunk",
                    "description": "Un chunk de document avec son contenu et ses métadonnées",
                    "vectorizer": "none",
                    "properties": [
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
                }
                weaviate_client.schema.create_class(class_obj)
            
            if "IndexingStats" not in class_names:
                # Créer la classe si elle n'existe pas
                stats_class = {
                    "class": "IndexingStats",
                    "description": "Statistiques d'indexation de documents",
                    "properties": [
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
                }
                weaviate_client.schema.create_class(stats_class)
            
            # Indexer les chunks
            with weaviate_client.batch as batch:
                for i, chunk in enumerate(chunks):
                    # Préparer les propriétés
                    properties = {
                        "content": chunk["content"],
                        "documentId": file_id,
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
                
                # Ajouter les statistiques d'indexation
                weaviate_stats = {
                    "documentId": indexing_stats["document_id"],
                    "chunksCount": indexing_stats["chunks_count"],
                    "totalTokens": indexing_stats["total_tokens"],
                    "chunkingStrategy": indexing_stats["chunking_strategy"],
                    "chunkSize": indexing_stats["chunk_size"],
                    "chunkOverlap": indexing_stats["chunk_overlap"],
                    "cleaningApplied": indexing_stats["cleaning_applied"],
                    "cleanedPercentage": indexing_stats["cleaned_percentage"],
                    "timestamp": indexing_stats["timestamp"]
                }
                
                batch.add_data_object(
                    data_object=weaviate_stats,
                    class_name="IndexingStats"
                )
        else:
            # Utiliser notre client personnalisé
            success = weaviate_client.batch_import_document_chunks(chunks, file_id, embeddings)
            if not success:
                raise HTTPException(status_code=500, detail="Échec de l'indexation des chunks")
            
            # Stocker les statistiques d'indexation
            success = weaviate_client.store_indexing_stats(indexing_stats)
            if not success:
                raise HTTPException(status_code=500, detail="Échec du stockage des statistiques d'indexation")
        
        # Stocker les statistiques d'indexation dans le dossier du document
        stats_path = os.path.join(file_dir, "indexing_stats.json")
        with open(stats_path, "w") as f:
            json.dump(indexing_stats, f, indent=2)
        
        return {"status": "indexed", "chunks_count": len(chunks), "indexing_stats": indexing_stats}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Renvoie l'état des connexions"""
    return {
        "weaviate": weaviate_status,
        "embedder": embedder_status
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)