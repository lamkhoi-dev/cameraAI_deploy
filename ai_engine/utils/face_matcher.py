"""
Face Matching Utility - Manage face embeddings and similarity matching
Supports in-memory and future database backends (Redis, pgvector)
"""

import json
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

from ..config import (
    FACE_EMBEDDING_DIM, FACE_SIMILARITY_THRESHOLD, FACE_VECTOR_DB_TYPE,
    KNOWN_FACES_DB_DIR
)


logger = logging.getLogger(__name__)


class FaceMatchingEngine:
    """
    Manage face embeddings and perform face matching
    
    Currently supports:
    - In-memory matching (fast, for single server)
    - JSON file storage (persistent)
    
    Future support:
    - Redis (distributed caching)
    - pgvector (PostgreSQL vector search)
    """
    
    def __init__(self, db_type: str = "memory"):
        """
        Initialize face matching engine
        
        Args:
            db_type: "memory", "redis", or "pgvector"
        """
        self.db_type = db_type
        self.known_faces: Dict[str, Dict] = {}  # person_id -> {embedding, metadata}
        self.embedding_dim = FACE_EMBEDDING_DIM
        self.similarity_threshold = FACE_SIMILARITY_THRESHOLD
        
        self._load_known_faces()
        logger.info(f"✓ Face matching engine initialized ({db_type} mode)")
    
    def add_known_face(self, person_id: str, embedding: List[float], metadata: Dict = None) -> bool:
        """
        Register a known face embedding
        
        Args:
            person_id: Unique person identifier
            embedding: 512-dimensional ArcFace embedding
            metadata: Additional metadata (name, age, etc.)
            
        Returns:
            True if successful
        """
        if not embedding or len(embedding) != self.embedding_dim:
            logger.warning(f"⚠️  Invalid embedding dimension: {len(embedding)}")
            return False
        
        try:
            self.known_faces[person_id] = {
                'embedding': embedding,
                'metadata': metadata or {},
                'added_at': datetime.utcnow().isoformat(),
                'match_count': 0
            }
            
            # Persist to disk
            self._save_known_faces()
            
            logger.info(f"✓ Registered known face: {person_id}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to add known face: {e}")
            return False
    
    def find_matching_face(self, query_embedding: List[float]) -> Optional[Dict]:
        """
        Find matching known face from query embedding
        
        Args:
            query_embedding: 512-dimensional embedding to search for
            
        Returns:
            Dict with best match: {person_id, similarity, metadata} or None
        """
        if not query_embedding or len(query_embedding) != self.embedding_dim:
            return None
        
        best_match = None
        best_similarity = self.similarity_threshold
        
        try:
            query_vec = np.array(query_embedding, dtype=np.float32)
            query_vec = query_vec / np.linalg.norm(query_vec)
            
            for person_id, face_data in self.known_faces.items():
                embedding = face_data['embedding']
                known_vec = np.array(embedding, dtype=np.float32)
                known_vec = known_vec / np.linalg.norm(known_vec)
                
                # Cosine similarity
                similarity = np.dot(query_vec, known_vec)
                similarity = (similarity + 1) / 2  # Normalize to [0, 1]
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        'person_id': person_id,
                        'similarity': float(best_similarity),
                        'metadata': face_data['metadata'],
                        'added_at': face_data['added_at']
                    }
            
            if best_match:
                # Update match count
                self.known_faces[best_match['person_id']]['match_count'] += 1
                logger.info(f"✓ Found face match: {best_match['person_id']} ({best_similarity:.2%} confidence)")
            
            return best_match
            
        except Exception as e:
            logger.error(f"✗ Face matching error: {e}")
            return None
    
    def batch_find_matching_faces(self, query_embeddings: List[List[float]], top_k: int = 1) -> List[Optional[Dict]]:
        """
        Find matching faces for multiple query embeddings
        
        Args:
            query_embeddings: List of 512-dimensional embeddings
            top_k: Return top K matches for each query
            
        Returns:
            List of match results (same length as query_embeddings)
        """
        results = []
        for embedding in query_embeddings:
            match = self.find_matching_face(embedding)
            results.append(match)
        return results
    
    def get_known_faces(self) -> Dict:
        """Return all known faces"""
        return self.known_faces.copy()
    
    def remove_known_face(self, person_id: str) -> bool:
        """Remove a known face from database"""
        if person_id in self.known_faces:
            del self.known_faces[person_id]
            self._save_known_faces()
            logger.info(f"✓ Removed known face: {person_id}")
            return True
        return False
    
    def clear_all_faces(self) -> bool:
        """Clear all known faces (use with caution)"""
        self.known_faces = {}
        self._save_known_faces()
        logger.info("⚠️  Cleared all known faces")
        return True
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        total_faces = len(self.known_faces)
        total_matches = sum(f['match_count'] for f in self.known_faces.values())
        
        return {
            'total_known_faces': total_faces,
            'total_matches': total_matches,
            'db_type': self.db_type,
            'embedding_dim': self.embedding_dim,
            'similarity_threshold': self.similarity_threshold
        }
    
    def _save_known_faces(self) -> bool:
        """Persist known faces to disk (JSON)"""
        try:
            KNOWN_FACES_DB_DIR.mkdir(exist_ok=True)
            
            db_file = KNOWN_FACES_DB_DIR / "known_faces.json"
            
            # Prepare data for JSON serialization
            data_to_save = {}
            for person_id, face_data in self.known_faces.items():
                data_to_save[person_id] = {
                    'embedding': face_data['embedding'],
                    'metadata': face_data['metadata'],
                    'added_at': face_data['added_at'],
                    'match_count': face_data['match_count']
                }
            
            with open(db_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to save known faces: {e}")
            return False
    
    def _load_known_faces(self) -> bool:
        """Load known faces from disk (JSON)"""
        try:
            db_file = KNOWN_FACES_DB_DIR / "known_faces.json"
            
            if not db_file.exists():
                logger.info("ℹ️  No known faces database found (first run)")
                return True
            
            with open(db_file, 'r') as f:
                data = json.load(f)
            
            for person_id, face_data in data.items():
                self.known_faces[person_id] = {
                    'embedding': face_data['embedding'],
                    'metadata': face_data.get('metadata', {}),
                    'added_at': face_data.get('added_at', ''),
                    'match_count': face_data.get('match_count', 0)
                }
            
            logger.info(f"✓ Loaded {len(self.known_faces)} known faces from database")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to load known faces: {e}")
            return False


# Global instance
_face_matching_engine: Optional[FaceMatchingEngine] = None


def get_face_matching_engine() -> FaceMatchingEngine:
    """Get or initialize global face matching engine"""
    global _face_matching_engine
    
    if _face_matching_engine is None:
        _face_matching_engine = FaceMatchingEngine(db_type=FACE_VECTOR_DB_TYPE)
    
    return _face_matching_engine
