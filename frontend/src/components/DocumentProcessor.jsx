import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Settings, Database, FileText } from 'lucide-react';
import { documentService, configService } from '../services/api';

// Configuration initiale
const DEFAULT_CONFIG = {
  chunking: {
    chunkSize: 800,
    overlapSize: 100,
    minChunkSize: 200,
    respectBoundaries: true,
    strategy: "semantic" // semantic, fixed, paragraph
  },
  embedding: {
    model: "voyagerai",
    dimensions: 1024
  },
  weaviate: {
    url: "",
    apiKey: ""
  },
  cleaning: {
    removeHeaders: true,
    removeFooters: true,
    removePageNumbers: true,
    removeExtraWhitespace: true,
    normalizeQuotes: true,
    fixHyphenation: true
  }
};

const DocumentProcessor = () => {
  // États
  const [files, setFiles] = useState([]);
  const [processingStatus, setProcessingStatus] = useState({});
  const [currentDocument, setCurrentDocument] = useState(null);
  const [documentChunks, setDocumentChunks] = useState([]);
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [weaviateStatus, setWeaviateStatus] = useState('disconnected');
  const [embeddingStatus, setEmbeddingStatus] = useState('disconnected');
  const [activeTab, setActiveTab] = useState('upload');
  const [previewMode, setPreviewMode] = useState('chunks');
  const [indexingStats, setIndexingStats] = useState(null);

  // Vérifier l'état de connexion au chargement
  useEffect(() => {
    const checkConnectionStatus = async () => {
      try {
        const status = await configService.getConnectionStatus();
        setWeaviateStatus(status.weaviate);
        setEmbeddingStatus(status.embedder);
      } catch (error) {
        console.error('Erreur lors de la vérification des connexions', error);
      }
    };
    
    checkConnectionStatus();
  }, []);

  // Fonction pour charger un document
  const handleFileUpload = async (e) => {
    const newFiles = Array.from(e.target.files);
    
    for (const file of newFiles) {
      try {
        setFiles(prev => [...prev, {
          file,
          id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          status: 'uploading',
          progress: 0,
          chunks: [],
          metadata: null
        }]);
        
        // Télécharger le fichier
        const uploadResult = await documentService.uploadFile(file);
        
        // Mettre à jour le statut
        setFiles(prev => prev.map(f => {
          if (f.file === file) {
            return {
              ...f,
              id: uploadResult.id,
              status: 'pending',
              progress: 0
            };
          }
          return f;
        }));
        
        // Traiter le document
        processDocument({
          file,
          id: uploadResult.id,
          status: 'pending'
        });
      } catch (error) {
        console.error('Erreur lors du téléchargement du fichier', error);
        
        // Mettre à jour le statut en cas d'erreur
        setFiles(prev => prev.map(f => {
          if (f.file === file) {
            return {
              ...f,
              status: 'error',
              error: error.message
            };
          }
          return f;
        }));
      }
    }
  };

  // Fonction de traitement d'un document
  const processDocument = useCallback(async (fileObj) => {
    try {
      // Marquer en cours de traitement
      setProcessingStatus(prev => ({
        ...prev,
        [fileObj.id]: { status: 'processing', progress: 0 }
      }));
      
      // Simuler une progression
      let progress = 0;
      const interval = setInterval(() => {
        progress += 5;
        if (progress <= 90) {
          setProcessingStatus(prev => ({
            ...prev,
            [fileObj.id]: { status: 'processing', progress }
          }));
        }
      }, 200);
      
      // Appeler l'API de traitement
      const result = await documentService.processDocument(fileObj.id, config);
      
      // Arrêter la simulation
      clearInterval(interval);
      
      // Mettre à jour le statut
      setProcessingStatus(prev => ({
        ...prev,
        [fileObj.id]: { status: 'completed', progress: 100 }
      }));
      
      // Mettre à jour l'état du fichier
      setFiles(prev => prev.map(f => {
        if (f.id === fileObj.id) {
          return {
            ...f,
            status: 'completed',
            chunks: result.chunks,
            metadata: result.metadata
          };
        }
        return f;
      }));
      
      // Si c'est le document actuel, mettre à jour les chunks
      if (currentDocument && currentDocument.id === fileObj.id) {
        setDocumentChunks(result.chunks);
      }
    } catch (error) {
      console.error('Erreur lors du traitement du document', error);
      
      setProcessingStatus(prev => ({
        ...prev,
        [fileObj.id]: { status: 'error', error: error.message }
      }));
      
      setFiles(prev => prev.map(f => {
        if (f.id === fileObj.id) {
          return {
            ...f,
            status: 'error',
            error: error.message
          };
        }
        return f;
      }));
    }
  }, [config, currentDocument]);

  // Traiter les documents téléchargés
  useEffect(() => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    
    pendingFiles.forEach(fileObj => {
      processDocument(fileObj);
    });
  }, [files, processDocument]);

  // Sélectionner un document pour affichage
  const handleSelectDocument = (fileObj) => {
    setCurrentDocument(fileObj);
    if (fileObj && fileObj.chunks) {
      setDocumentChunks(fileObj.chunks);
    } else {
      setDocumentChunks([]);
    }
  };

  // Mettre à jour la configuration
  const handleConfigChange = (section, key, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  // Reconnecter et transformer les chunks
  const reprocessCurrentDocument = async () => {
    if (!currentDocument) return;
    
    try {
      // Marquer en cours de traitement
      setProcessingStatus(prev => ({
        ...prev,
        [currentDocument.id]: { status: 'reprocessing', progress: 0 }
      }));
      
      // Simuler une progression
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        if (progress <= 90) {
          setProcessingStatus(prev => ({
            ...prev,
            [currentDocument.id]: { status: 'reprocessing', progress }
          }));
        }
      }, 100);
      
      // Appeler l'API de traitement
      const result = await documentService.processDocument(currentDocument.id, config);
      
      // Arrêter la simulation
      clearInterval(interval);
      
      // Mettre à jour le statut
      setProcessingStatus(prev => ({
        ...prev,
        [currentDocument.id]: { status: 'completed', progress: 100 }
      }));
      
      // Mettre à jour l'état du fichier
      setFiles(prev => prev.map(f => {
        if (f.id === currentDocument.id) {
          return {
            ...f,
            status: 'completed',
            chunks: result.chunks,
            metadata: result.metadata
          };
        }
        return f;
      }));
      
      // Mettre à jour les chunks affichés
      setDocumentChunks(result.chunks);
    } catch (error) {
      console.error('Erreur lors du retraitement du document', error);
      
      setProcessingStatus(prev => ({
        ...prev,
        [currentDocument.id]: { status: 'error', error: error.message }
      }));
    }
  };

  // Connecter à Weaviate
  const connectToWeaviate = async () => {
    try {
      setWeaviateStatus('connecting');
      
      // Appeler l'API de connexion
      await configService.connectToWeaviate(config.weaviate);
      
      setWeaviateStatus('connected');
    } catch (error) {
      console.error('Erreur lors de la connexion à Weaviate', error);
      setWeaviateStatus('disconnected');
      alert(`Erreur de connexion à Weaviate: ${error.message}`);
    }
  };

  // Connecter à l'embedder
  const connectToEmbedder = async () => {
    try {
      setEmbeddingStatus('connecting');
      
      // Appeler l'API de connexion
      await configService.connectToEmbedder(config.embedding);
      
      setEmbeddingStatus('connected');
    } catch (error) {
      console.error('Erreur lors de la connexion à l\'embedder', error);
      setEmbeddingStatus('disconnected');
      alert(`Erreur de connexion à l'embedder: ${error.message}`);
    }
  };

  // Envoyer les chunks à Weaviate
  const sendToWeaviate = async () => {
    if (!currentDocument || weaviateStatus !== 'connected' || embeddingStatus !== 'connected') return;
    
    try {
      // Marquer en cours d'indexation
      setProcessingStatus(prev => ({
        ...prev,
        [currentDocument.id]: { status: 'indexing', progress: 0 }
      }));
      
      // Simuler une progression
      let progress = 0;
      const interval = setInterval(() => {
        progress += 5;
        if (progress <= 90) {
          setProcessingStatus(prev => ({
            ...prev,
            [currentDocument.id]: { status: 'indexing', progress }
          }));
        }
      }, 200);
      
      // Appeler l'API d'indexation
      const result = await documentService.indexDocument(currentDocument.id);
      
      // Arrêter la simulation
      clearInterval(interval);
      
      // Mettre à jour le statut
      setProcessingStatus(prev => ({
        ...prev,
        [currentDocument.id]: { status: 'indexed', progress: 100 }
      }));
      
      // Enregistrer les statistiques d'indexation
      setIndexingStats(result.indexing_stats);
      
      // Mettre à jour l'état du fichier
      setFiles(prev => prev.map(f => {
        if (f.id === currentDocument.id) {
          return {
            ...f,
            status: 'indexed',
            indexingStats: result.indexing_stats
          };
        }
        return f;
      }));
    } catch (error) {
      console.error('Erreur lors de l\'indexation dans Weaviate', error);
      
      setProcessingStatus(prev => ({
        ...prev,
        [currentDocument.id]: { status: 'error', error: error.message }
      }));
      
      alert(`Erreur d'indexation: ${error.message}`);
    }
  };

  // Rendu de l'interface
  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* En-tête */}
      <header className="bg-white shadow-sm px-6 py-4 border-b">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-semibold text-gray-800">Document Processor pour Systémique</h1>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <div className={`h-2 w-2 rounded-full ${weaviateStatus === 'connected' ? 'bg-green-500' : weaviateStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-500">Weaviate</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className={`h-2 w-2 rounded-full ${embeddingStatus === 'connected' ? 'bg-green-500' : embeddingStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-500">Embedder</span>
            </div>
            <button 
              onClick={() => setSettingsOpen(!settingsOpen)}
              className="p-2 rounded hover:bg-gray-100"
            >
              <Settings size={18} />
            </button>
          </div>
        </div>
      </header>

      {/* Corps principal */}
      <div className="flex flex-1 overflow-hidden">
        {/* Barre latérale */}
        <aside className="w-64 bg-white border-r">
          <div className="p-4 border-b">
            <ul className="flex space-x-2">
              <li>
                <button 
                  onClick={() => setActiveTab('upload')}
                  className={`px-3 py-1.5 rounded text-sm ${activeTab === 'upload' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  Documents
                </button>
              </li>
              <li>
                <button 
                  onClick={() => setActiveTab('preview')}
                  className={`px-3 py-1.5 rounded text-sm ${activeTab === 'preview' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                  Prévisualisation
                </button>
              </li>
            </ul>
          </div>

          {activeTab === 'upload' && (
            <>
              {/* Zone de téléchargement */}
              <div className="p-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                  <Upload className="mx-auto h-8 w-8 text-gray-400" />
                  <p className="mt-1 text-sm text-gray-500">Glissez des fichiers ici ou</p>
                  <label className="mt-2 inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 cursor-pointer">
                    Sélectionner des fichiers
                    <input
                      type="file"
                      className="hidden"
                      multiple
                      onChange={handleFileUpload}
                    />
                  </label>
                </div>
              </div>

              {/* Liste des fichiers */}
              <div className="overflow-y-auto">
                <h2 className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Documents ({files.length})</h2>
                <ul className="space-y-1 px-2">
                  {files.map(fileObj => (
                    <li 
                      key={fileObj.id}
                      className={`px-2 py-2 rounded-md text-sm cursor-pointer ${currentDocument?.id === fileObj.id ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                      onClick={() => handleSelectDocument(fileObj)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2 overflow-hidden">
                          <FileText size={16} className="text-gray-500 flex-shrink-0" />
                          <span className="truncate">{fileObj.file.name}</span>
                        </div>
                        <div>
                          {fileObj.status === 'pending' && (
                            <div className="h-2 w-2 rounded-full bg-gray-300"></div>
                          )}
                          {(fileObj.status === 'processing' || fileObj.status === 'reprocessing' || fileObj.status === 'indexing') && (
                            <div className="h-2 w-2 rounded-full bg-yellow-400"></div>
                          )}
                          {fileObj.status === 'completed' && (
                            <div className="h-2 w-2 rounded-full bg-green-500"></div>
                          )}
                          {fileObj.status === 'indexed' && (
                            <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                          )}
                        </div>
                      </div>
                      {(processingStatus[fileObj.id]?.status === 'processing' || 
                        processingStatus[fileObj.id]?.status === 'reprocessing' ||
                        processingStatus[fileObj.id]?.status === 'indexing') && (
                        <div className="mt-1">
                          <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${processingStatus[fileObj.id]?.status === 'indexing' ? 'bg-blue-500' : 'bg-yellow-500'}`} 
                              style={{ width: `${processingStatus[fileObj.id]?.progress || 0}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}

          {activeTab === 'preview' && currentDocument && (
            <div className="p-4">
              <h3 className="font-medium text-gray-700 mb-2">Options d'affichage</h3>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <input 
                    id="chunks-view" 
                    type="radio" 
                    name="view-mode" 
                    checked={previewMode === 'chunks'} 
                    onChange={() => setPreviewMode('chunks')}
                  />
                  <label htmlFor="chunks-view" className="text-sm">Chunks</label>
                </div>
                <div className="flex items-center space-x-2">
                  <input 
                    id="metadata-view" 
                    type="radio" 
                    name="view-mode" 
                    checked={previewMode === 'metadata'} 
                    onChange={() => setPreviewMode('metadata')}
                  />
                  <label htmlFor="metadata-view" className="text-sm">Métadonnées</label>
                </div>
                <div className="flex items-center space-x-2">
                  <input 
                    id="stats-view" 
                    type="radio" 
                    name="view-mode" 
                    checked={previewMode === 'stats'} 
                    onChange={() => setPreviewMode('stats')}
                  />
                  <label htmlFor="stats-view" className="text-sm">Statistiques d'indexation</label>
                </div>
              </div>
              
              <h3 className="font-medium text-gray-700 mt-6 mb-2">Nettoyage du document</h3>
              <div className="space-y-2 mb-6">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="remove-headers"
                    checked={config.cleaning.removeHeaders}
                    onChange={(e) => handleConfigChange('cleaning', 'removeHeaders', e.target.checked)}
                  />
                  <label htmlFor="remove-headers" className="text-xs">Supprimer les en-têtes</label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="remove-footers"
                    checked={config.cleaning.removeFooters}
                    onChange={(e) => handleConfigChange('cleaning', 'removeFooters', e.target.checked)}
                  />
                  <label htmlFor="remove-footers" className="text-xs">Supprimer les pieds de page</label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="remove-page-numbers"
                    checked={config.cleaning.removePageNumbers}
                    onChange={(e) => handleConfigChange('cleaning', 'removePageNumbers', e.target.checked)}
                  />
                  <label htmlFor="remove-page-numbers" className="text-xs">Supprimer les numéros de page</label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="fix-hyphenation"
                    checked={config.cleaning.fixHyphenation}
                    onChange={(e) => handleConfigChange('cleaning', 'fixHyphenation', e.target.checked)}
                  />
                  <label htmlFor="fix-hyphenation" className="text-xs">Corriger les coupures de mots</label>
                </div>
              </div>
              
              <h3 className="font-medium text-gray-700 mt-6 mb-2">Paramètres de chunking</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Taille des chunks</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="range"
                      min="200"
                      max="2000"
                      step="100"
                      value={config.chunking.chunkSize}
                      onChange={(e) => handleConfigChange('chunking', 'chunkSize', parseInt(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">{config.chunking.chunkSize}</span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Chevauchement</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="range"
                      min="0"
                      max="300"
                      step="10"
                      value={config.chunking.overlapSize}
                      onChange={(e) => handleConfigChange('chunking', 'overlapSize', parseInt(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">{config.chunking.overlapSize}</span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Stratégie</label>
                  <select
                    value={config.chunking.strategy}
                    onChange={(e) => handleConfigChange('chunking', 'strategy', e.target.value)}
                    className="w-full px-3 py-1.5 text-sm border rounded"
                  >
                    <option value="semantic">Sémantique</option>
                    <option value="fixed">Taille fixe</option>
                    <option value="paragraph">Paragraphe</option>
                  </select>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="respect-boundaries"
                    checked={config.chunking.respectBoundaries}
                    onChange={(e) => handleConfigChange('chunking', 'respectBoundaries', e.target.checked)}
                  />
                  <label htmlFor="respect-boundaries" className="text-xs">Respecter les frontières</label>
                </div>
                
                <button
                  onClick={reprocessCurrentDocument}
                  className="w-full px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Appliquer les changements
                </button>
              </div>
            </div>
          )}
        </aside>

        {/* Zone principale */}
        <main className="flex-1 overflow-hidden flex flex-col">
          {currentDocument ? (
            <>
              {/* En-tête du document */}
              <div className="border-b bg-white p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="font-medium">{currentDocument.file.name}</h2>
                    <div className="flex items-center text-sm text-gray-500 mt-1">
                      <span className="mr-3">{(currentDocument.file.size / 1024).toFixed(1)} KB</span>
                      {currentDocument.chunks && (
                        <span className="mr-3">{currentDocument.chunks.length} chunks</span>
                      )}
                      {currentDocument.metadata?.language && (
                        <span>{currentDocument.metadata.language}</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    {weaviateStatus === 'connected' && embeddingStatus === 'connected' && (
                      <button
                        onClick={sendToWeaviate}
                        className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 flex items-center"
                        disabled={currentDocument.status === 'indexed'}
                      >
                        <Database size={16} className="mr-1" />
                        {currentDocument.status === 'indexed' ? 'Indexé' : 'Envoyer à Weaviate'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Contenu du document */}
              <div className="flex-1 overflow-auto p-6">
                {previewMode === 'chunks' && documentChunks.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-800 mb-4">Prévisualisation des chunks ({documentChunks.length})</h3>
                    
                    {documentChunks.map((chunk, index) => (
                      <div key={chunk.id} className="border rounded-lg overflow-hidden">
                        <div className="bg-gray-50 px-4 py-2 border-b flex justify-between items-center">
                          <div className="font-medium text-gray-700">Chunk {index + 1}</div>
                          <div className="text-sm text-gray-500">
                            {chunk.metadata?.page_range && (
                              <span className="mr-3">Pages: {chunk.metadata.page_range}</span>
                            )}
                            {chunk.metadata?.section && (
                              <span className="mr-3">Section: {chunk.metadata.section}</span>
                            )}
                          </div>
                        </div>
                        <div className="p-4 bg-white">
                          <p className="text-sm text-gray-800 whitespace-pre-wrap">{chunk.content}</p>
                          
                          {chunk.metadata?.key_concepts && (
                            <div className="mt-3 flex flex-wrap gap-1">
                              {chunk.metadata.key_concepts.map(concept => (
                                <span key={concept} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                                  {concept}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {previewMode === 'metadata' && currentDocument.metadata && (
                  <div className="bg-white rounded-lg border p-6">
                    <h3 className="text-lg font-medium text-gray-800 mb-6">Métadonnées extraites</h3>
                    
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Informations générales</h4>
                        <table className="w-full">
                          <tbody>
                            {Object.entries(currentDocument.metadata)
                              .filter(([key]) => !Array.isArray(currentDocument.metadata[key]) && typeof currentDocument.metadata[key] !== 'object')
                              .map(([key, value]) => (
                                <tr key={key} className="border-b">
                                  <td className="py-2 text-sm font-medium text-gray-500">{key}</td>
                                  <td className="py-2 text-sm text-gray-800">{value}</td>
                                </tr>
                              ))}
                          </tbody>
                        </table>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Concepts extraits</h4>
                        {currentDocument.metadata.concepts && (
                          <div className="flex flex-wrap gap-1 mb-6">
                            {currentDocument.metadata.concepts.map(concept => (
                              <span key={concept} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                                {concept}
                              </span>
                            ))}
                          </div>
                        )}
                        
                        <h4 className="font-medium text-gray-700 mb-2 mt-6">Auteurs</h4>
                        {currentDocument.metadata.authors && (
                          <div>
                            {currentDocument.metadata.authors.map(author => (
                              <div key={author} className="py-1 text-sm text-gray-800">
                                {author}
                              </div>
                            ))}
                          </div>
                        )}

                        {currentDocument.metadata.document_structure && (
                          <>
                            <h4 className="font-medium text-gray-700 mb-2 mt-6">Structure du document</h4>
                            <div className="space-y-2">
                              {currentDocument.metadata.document_structure.chapters && (
                                <div>
                                  <h5 className="text-sm font-medium">Chapitres ({currentDocument.metadata.document_structure.chapters.length})</h5>
                                  <ul className="pl-4 mt-1">
                                    {currentDocument.metadata.document_structure.chapters.slice(0, 3).map((chapter, idx) => (
                                      <li key={idx} className="text-xs text-gray-700">{chapter.title}</li>
                                    ))}
                                    {currentDocument.metadata.document_structure.chapters.length > 3 && (
                                      <li className="text-xs text-gray-500 italic">+ {currentDocument.metadata.document_structure.chapters.length - 3} autres...</li>
                                    )}
                                  </ul>
                                </div>
                              )}

                              {currentDocument.metadata.document_structure.sections && (
                                <div>
                                  <h5 className="text-sm font-medium">Sections ({currentDocument.metadata.document_structure.sections.length})</h5>
                                  <ul className="pl-4 mt-1">
                                    {currentDocument.metadata.document_structure.sections.slice(0, 3).map((section, idx) => (
                                      <li key={idx} className="text-xs text-gray-700">{section.title}</li>
                                    ))}
                                    {currentDocument.metadata.document_structure.sections.length > 3 && (
                                      <li className="text-xs text-gray-500 italic">+ {currentDocument.metadata.document_structure.sections.length - 3} autres...</li>
                                    )}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    </div>

                    {currentDocument.metadata.cleaning_stats && (
                      <div className="mt-8">
                        <h4 className="font-medium text-gray-700 mb-2">Statistiques de nettoyage</h4>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-gray-50 p-3 rounded">
                            <div className="text-sm text-gray-500">Texte original</div>
                            <div className="text-lg font-medium">{currentDocument.metadata.cleaning_stats.original_length} caractères</div>
                          </div>
                          <div className="bg-gray-50 p-3 rounded">
                            <div className="text-sm text-gray-500">Texte nettoyé</div>
                            <div className="text-lg font-medium">{currentDocument.metadata.cleaning_stats.cleaned_length} caractères</div>
                          </div>
                          <div className="bg-gray-50 p-3 rounded">
                            <div className="text-sm text-gray-500">Bruit supprimé</div>
                            <div className="text-lg font-medium">{currentDocument.metadata.cleaning_stats.reduction_percentage}%</div>
                          </div>
                        </div>
                        <div className="mt-4">
                          <h5 className="text-sm font-medium mb-2">Éléments supprimés</h5>
                          <div className="flex flex-wrap gap-1">
                            {currentDocument.metadata.cleaning_stats.removed_elements.map(element => (
                              <span key={element} className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                                {element}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {previewMode === 'stats' && currentDocument && currentDocument.indexingStats && (
                  <div className="bg-white rounded-lg border p-6">
                    <h3 className="text-lg font-medium text-gray-800 mb-6">Statistiques d'indexation dans Weaviate</h3>
                    
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Statistiques de chunking</h4>
                        <table className="w-full">
                          <tbody>
                            <tr className="border-b">
                              <td className="py-2 text-sm font-medium text-gray-500">Nombre de chunks</td>
                              <td className="py-2 text-sm text-gray-800">{currentDocument.indexingStats.chunks_count}</td>
                            </tr>
                            <tr className="border-b">
                              <td className="py-2 text-sm font-medium text-gray-500">Nombre total de tokens</td>
                              <td className="py-2 text-sm text-gray-800">{currentDocument.indexingStats.total_tokens}</td>
                            </tr>
                            <tr className="border-b">
                              <td className="py-2 text-sm font-medium text-gray-500">Stratégie de chunking</td>
                              <td className="py-2 text-sm text-gray-800">{currentDocument.indexingStats.chunking_strategy}</td>
                            </tr>
                            <tr className="border-b">
                              <td className="py-2 text-sm font-medium text-gray-500">Taille des chunks</td>
                              <td className="py-2 text-sm text-gray-800">{currentDocument.indexingStats.chunk_size}</td>
                            </tr>
                            <tr className="border-b">
                              <td className="py-2 text-sm font-medium text-gray-500">Chevauchement</td>
                              <td className="py-2 text-sm text-gray-800">{currentDocument.indexingStats.chunk_overlap}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-700 mb-2">Statistiques de nettoyage</h4>
                        <table className="w-full">
                          <tbody>
                            <tr className="border-b">
                              <td className="py-2 text-sm font-medium text-gray-500">Nettoyage appliqué</td>
                              <td className="py-2 text-sm text-gray-800">{currentDocument.indexingStats.cleaning_applied ? "Oui" : "Non"}</td>
                            </tr>
                            <tr className="border-b">
                              <td className="py-2 text-sm font-medium text-gray-500">Pourcentage de texte supprimé</td>
                              <td className="py-2 text-sm text-gray-800">{currentDocument.indexingStats.cleaned_percentage}%</td>
                            </tr>
                            <tr className="border-b">
                              <td className="py-2 text-sm font-medium text-gray-500">Date d'indexation</td>
                              <td className="py-2 text-sm text-gray-800">{new Date(currentDocument.indexingStats.timestamp).toLocaleString()}</td>
                            </tr>
                          </tbody>
                        </table>
                        
                        <div className="mt-6">
                          <h4 className="font-medium text-gray-700 mb-2">Graphique d'information</h4>
                          <div className="flex flex-col space-y-2">
                            <div className="flex items-center space-x-2">
                              <div className="text-xs w-28">Texte conservé</div>
                              <div className="flex-1 bg-gray-200 h-4 rounded-full overflow-hidden">
                                <div 
                                  className="bg-green-500 h-full" 
                                  style={{ width: `${100 - currentDocument.indexingStats.cleaned_percentage}%` }}
                                ></div>
                              </div>
                              <div className="text-xs w-12">{100 - currentDocument.indexingStats.cleaned_percentage}%</div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <div className="text-xs w-28">Bruit supprimé</div>
                              <div className="flex-1 bg-gray-200 h-4 rounded-full overflow-hidden">
                                <div 
                                  className="bg-red-400 h-full" 
                                  style={{ width: `${currentDocument.indexingStats.cleaned_percentage}%` }}
                                ></div>
                              </div>
                              <div className="text-xs w-12">{currentDocument.indexingStats.cleaned_percentage}%</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center flex-col p-6 text-center">
              <FileText size={48} className="text-gray-300 mb-4" />
              <h3 className="text-xl font-medium text-gray-400">Aucun document sélectionné</h3>
              <p className="mt-2 text-gray-500 max-w-md">
                Sélectionnez un document dans le panneau de gauche pour voir son contenu et ses chunks.
              </p>
            </div>
          )}
        </main>
      </div>

      {/* Modal de configuration */}
      {settingsOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-auto">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h3 className="font-medium text-lg">Configuration</h3>
              <button 
                onClick={() => setSettingsOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                &times;
              </button>
            </div>
            
            <div className="p-6">
              <div className="space-y-6">
                {/* Configuration de l'embedder */}
                <div>
                  <h4 className="font-medium text-gray-800 mb-3">Configuration de l'embedder</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Modèle</label>
                      <select
                        value={config.embedding.model}
                        onChange={(e) => handleConfigChange('embedding', 'model', e.target.value)}
                        className="w-full px-3 py-2 border rounded"
                      >
                        <option value="voyagerai">VoyageAI</option>
                        <option value="openai">OpenAI</option>
                        <option value="cohere">Cohere</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Dimensions</label>
                      <select
                        value={config.embedding.dimensions}
                        onChange={(e) => handleConfigChange('embedding', 'dimensions', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border rounded"
                      >
                        <option value={256}>256</option>
                        <option value={512}>512</option>
                        <option value={1024}>1024 (recommandé)</option>
                        <option value={2048}>2048</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Clé API</label>
                      <div className="flex">
                        <input
                          type="password"
                          placeholder="Clé API de l'embedder"
                          className="flex-1 px-3 py-2 border rounded-l"
                          onChange={(e) => handleConfigChange('embedding', 'apiKey', e.target.value)}
                        />
                        <button
                          onClick={connectToEmbedder}
                          className={`px-4 py-2 text-white rounded-r ${
                            embeddingStatus === 'connected' 
                              ? 'bg-green-600' 
                              : embeddingStatus === 'connecting' 
                                ? 'bg-yellow-500' 
                                : 'bg-blue-600 hover:bg-blue-700'
                          }`}
                        >
                          {embeddingStatus === 'connected' 
                            ? 'Connecté' 
                            : embeddingStatus === 'connecting' 
                              ? 'Connexion...' 
                              : 'Connecter'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Configuration de Weaviate */}
                <div>
                  <h4 className="font-medium text-gray-800 mb-3">Configuration de Weaviate</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">URL du cluster</label>
                      <input
                        type="text"
                        placeholder="https://your-cluster.weaviate.network"
                        value={config.weaviate.url}
                        onChange={(e) => handleConfigChange('weaviate', 'url', e.target.value)}
                        className="w-full px-3 py-2 border rounded"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Clé API</label>
                      <div className="flex">
                        <input
                          type="password"
                          placeholder="Clé API Weaviate"
                          className="flex-1 px-3 py-2 border rounded-l"
                          onChange={(e) => handleConfigChange('weaviate', 'apiKey', e.target.value)}
                        />
                        <button
                          onClick={connectToWeaviate}
                          className={`px-4 py-2 text-white rounded-r ${
                            weaviateStatus === 'connected' 
                              ? 'bg-green-600' 
                              : weaviateStatus === 'connecting' 
                                ? 'bg-yellow-500' 
                                : 'bg-blue-600 hover:bg-blue-700'
                          }`}
                        >
                          {weaviateStatus === 'connected' 
                            ? 'Connecté' 
                            : weaviateStatus === 'connecting' 
                              ? 'Connexion...' 
                              : 'Connecter'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSettingsOpen(false)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Enregistrer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentProcessor;