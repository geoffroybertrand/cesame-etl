import axios from 'axios';

// URL de base de l'API
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Instance Axios avec configuration de base
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Service pour les opérations liées aux documents
export const documentService = {
  // Télécharger un fichier
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    };
    
    const response = await apiClient.post('/upload', formData, config);
    return response.data;
  },
  
  // Traiter un document
  processDocument: async (fileId, config) => {
    const response = await apiClient.post(`/process/${fileId}`, config);
    return response.data;
  },
  
  // Indexer un document dans Weaviate
  indexDocument: async (fileId) => {
    const response = await apiClient.post(`/index/${fileId}`);
    return response.data;
  },
};

// Service pour les opérations liées à la configuration
export const configService = {
  // Connecter à Weaviate
  connectToWeaviate: async (weaviateConfig) => {
    const response = await apiClient.post('/connect/weaviate', weaviateConfig);
    return response.data;
  },
  
  // Connecter au service d'embedding
  connectToEmbedder: async (embeddingConfig) => {
    const response = await apiClient.post('/connect/embedder', embeddingConfig);
    return response.data;
  },
  
  // Obtenir l'état des connexions
  getConnectionStatus: async () => {
    const response = await apiClient.get('/status');
    return response.data;
  },
};