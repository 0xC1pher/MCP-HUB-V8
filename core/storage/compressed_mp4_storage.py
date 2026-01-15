"""
Compressed MP4 Storage for MCP v6
Extends MP4Storage with vector compression capabilities
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

from .mp4_storage import MP4Storage, VirtualChunk
from .compressed_storage import VectorCompressor

logger = logging.getLogger(__name__)


class CompressedMP4Storage(MP4Storage):
    """
    Extended MP4 storage with vector compression support
    Maintains backward compatibility with existing MP4 files
    """
    
    def __init__(self, mp4_path: str, compression_config: Optional[Dict] = None):
        """
        Initialize compressed MP4 storage
        
        Args:
            mp4_path: Path to MP4 file
            compression_config: Optional compression configuration
        """
        super().__init__(mp4_path)
        
        # Initialize compressor if config provided
        if compression_config:
            self.compressor = VectorCompressor(compression_config)
            logger.info(f"CompressedMP4Storage initialized with compression: {compression_config}")
        else:
            self.compressor = None
            logger.info("CompressedMP4Storage initialized without compression (backward compatible)")
    
    def create_compressed_snapshot(self, chunks: List[VirtualChunk], vectors: np.ndarray, 
                                 hnsw_blob: bytes, metadata: Dict) -> str:
        """
        Create snapshot with compressed vectors
        
        Args:
            chunks: List of virtual chunks
            vectors: Vector embeddings (float32)
            hnsw_blob: HNSW index blob
            metadata: Additional metadata
            
        Returns:
            Snapshot hash
        """
        if self.compressor and len(vectors) > 0:
            # Compress vectors
            compressed_vectors, compression_metadata = self.compressor.compress_vectors(vectors)
            
            # Add compression info to metadata
            metadata['vector_compression'] = compression_metadata
            metadata['compressed_vectors_size'] = len(compressed_vectors)
            metadata['original_vectors_size'] = vectors.nbytes
            metadata['compression_enabled'] = True
            
            logger.info(f"Vectors compressed from {vectors.nbytes} to {len(compressed_vectors)} bytes "
                       f"({compression_metadata['compression_ratio']:.1%} ratio)")
            
            # Use compressed vectors as blob
            vectors_blob = compressed_vectors
        else:
            # No compression - convert to float32 bytes
            vectors_blob = vectors.astype(np.float32).tobytes()
            metadata['compression_enabled'] = False
            logger.info(f"Vectors stored without compression ({len(vectors_blob)} bytes)")
        
        # Call parent method to create snapshot
        return super().create_snapshot(chunks, vectors_blob, hnsw_blob, metadata)
    
    def load_compressed_snapshot(self) -> bool:
        """
        Load snapshot with automatic decompression if needed
        
        Returns:
            True if loaded successfully
        """
        # First try to load normally
        if not super().load_snapshot():
            return False
        
        # Check if compression was used
        if self.metadata.get('compression_enabled', False):
            logger.info("Loading compressed vectors from MP4")
            
            # Get compression metadata
            compression_metadata = self.metadata.get('vector_compression', {})
            
            if compression_metadata:
                # Read compressed vector blob
                vec_offset, vec_size = self.get_vector_blob_offset()
                
                if vec_size > 0 and self.mmap_data:
                    compressed_bytes = self.mmap_data[vec_offset:vec_offset + vec_size]
                    
                    # Decompress vectors
                    if self.compressor:
                        decompressed_vectors = self.compressor.decompress_vectors(
                            compressed_bytes, compression_metadata
                        )
                        
                        # Store decompressed vectors for access
                        self._decompressed_vectors = decompressed_vectors
                        logger.info(f"Decompressed {len(decompressed_vectors)} vectors successfully")
                        
                        return True
                    else:
                        logger.warning("Compressor not available for decompression")
        
        return True
    
    def get_vectors(self) -> Optional[np.ndarray]:
        """
        Get decompressed vectors (if compression was used)
        
        Returns:
            Vector array or None if not available
        """
        # Check if we have decompressed vectors cached
        if hasattr(self, '_decompressed_vectors'):
            return self._decompressed_vectors
        
        # Fallback to reading raw vectors (for uncompressed files)
        vec_offset, vec_size = self.get_vector_blob_offset()
        
        if vec_size > 0 and self.mmap_data:
            vector_bytes = self.mmap_data[vec_offset:vec_offset + vec_size]
            
            # Check if this is compressed data
            if self.metadata.get('compression_enabled', False):
                if self.compressor:
                    compression_metadata = self.metadata.get('vector_compression', {})
                    decompressed_vectors = self.compressor.decompress_vectors(
                        vector_bytes, compression_metadata
                    )
                    self._decompressed_vectors = decompressed_vectors
                    return decompressed_vectors
                else:
                    logger.error("Cannot decompress vectors - compressor not available")
                    return None
            else:
                # Uncompressed float32 vectors
                dimension = self.metadata.get('vector_dimension', 384)
                total_vectors = self.metadata.get('total_vectors', 0)
                
                vectors = np.frombuffer(vector_bytes, dtype=np.float32)
                vectors = vectors.reshape(total_vectors, dimension)
                return vectors
        
        return None
    
    def get_compression_stats(self) -> Optional[Dict]:
        """
        Get compression statistics for the current snapshot
        
        Returns:
            Statistics dict or None if not compressed
        """
        if not self.metadata.get('compression_enabled', False):
            return None
        
        compression_metadata = self.metadata.get('vector_compression', {})
        original_size = self.metadata.get('original_vectors_size', 0)
        compressed_size = self.metadata.get('compressed_vectors_size', 0)
        
        if original_size > 0 and compressed_size > 0:
            return {
                'original_size_bytes': original_size,
                'compressed_size_bytes': compressed_size,
                'compression_ratio': compressed_size / original_size,
                'space_saved_percent': (1 - compressed_size / original_size) * 100,
                'techniques_used': compression_metadata.get('compression_steps', []),
                'precision': compression_metadata.get('precision', 'unknown')
            }
        
        return None
    
    def create_snapshot_with_stats(self, chunks: List[VirtualChunk], vectors: np.ndarray,
                                 hnsw_blob: bytes, metadata: Dict) -> Tuple[str, Optional[Dict]]:
        """
        Create snapshot and return compression statistics
        
        Args:
            chunks: List of virtual chunks
            vectors: Vector embeddings
            hnsw_blob: HNSW index blob
            metadata: Additional metadata
            
        Returns:
            Tuple of (snapshot_hash, compression_stats)
        """
        snapshot_hash = self.create_compressed_snapshot(chunks, vectors, hnsw_blob, metadata)
        stats = self.get_compression_stats()
        
        return snapshot_hash, stats