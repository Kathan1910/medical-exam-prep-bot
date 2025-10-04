# storage/vector_store.py
import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class LocalVectorStore:
    """FAISS-based local vector store"""
    
    def __init__(self, dimension: int = 3072):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata: List[Dict[str, Any]] = []
        
    def add_embeddings(
        self, 
        embeddings: List[List[float]], 
        metadata_list: List[Dict[str, Any]]
    ) -> None:
        """Add embeddings with metadata to the index"""
        if not embeddings:
            logger.warning("No embeddings to add")
            return
        
        embeddings_array = np.array(embeddings).astype('float32')
        
        if embeddings_array.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embeddings_array.shape[1]} "
                f"does not match index dimension {self.dimension}"
            )
        
        self.index.add(embeddings_array)
        self.metadata.extend(metadata_list)
        
        logger.info(f"Added {len(embeddings)} embeddings to index")
    
    def search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        filter_chapter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        query_array = np.array([query_embedding]).astype('float32')
        
        # Search with buffer for filtering
        search_k = k * 3 if filter_chapter else k
        distances, indices = self.index.search(query_array, search_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= len(self.metadata):
                continue
                
            meta = self.metadata[idx]
            
            # Apply chapter filter
            if filter_chapter and meta.get('chapter_id') != filter_chapter:
                continue
            
            results.append({
                'metadata': meta,
                'score': float(dist),
                'index': int(idx)
            })
            
            if len(results) >= k:
                break
        
        logger.info(f"Found {len(results)} results for query")
        return results
    
    def save(self, path: Path) -> None:
        """Save index and metadata to disk"""
        path.mkdir(parents=True, exist_ok=True)
        
        index_path = path / "faiss.index"
        metadata_path = path / "metadata.pkl"
        
        faiss.write_index(self.index, str(index_path))
        
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        logger.info(f"Saved index with {self.index.ntotal} vectors to {path}")
    
    def load(self, path: Path) -> bool:
        """Load index and metadata from disk"""
        index_path = path / "faiss.index"
        metadata_path = path / "metadata.pkl"
        
        if not index_path.exists() or not metadata_path.exists():
            logger.warning(f"Index files not found at {path}")
            return False
        
        try:
            self.index = faiss.read_index(str(index_path))
            
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            logger.info(f"Loaded index with {self.index.ntotal} vectors from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'total_metadata': len(self.metadata)
        }