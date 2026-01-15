"""
Compressed Vector Storage for MCP v6
Implements various compression techniques for vector embeddings
"""

import numpy as np
import lz4.frame
import logging
from typing import Dict, Tuple, Optional
from sklearn.cluster import MiniBatchKMeans

logger = logging.getLogger(__name__)


class VectorCompressor:
    """
    Advanced vector compression using multiple techniques:
    1. Precision reduction (float32 -> float16 -> int8)
    2. Quantization (scalar and product quantization)
    3. Lossless compression (LZ4)
    """
    
    def __init__(self, config: Dict):
        """
        Initialize compressor with configuration
        
        Args:
            config: Configuration dict with compression parameters
        """
        self.precision = config.get('precision', 'float16')  # float32, float16, int8
        self.use_quantization = config.get('use_quantization', False)
        self.quantization_bits = config.get('quantization_bits', 8)  # 1-8 bits
        self.use_lz4 = config.get('use_lz4', True)
        self.quantizer = None
        
        # For product quantization
        self.pq_subvectors = config.get('pq_subvectors', 4)  # Divide vector into sub-vectors
        self.pq_clusters = config.get('pq_clusters', 256)  # Number of clusters per sub-vector
        
        logger.info(f"VectorCompressor initialized with precision={self.precision}, "
                   f"quantization={self.use_quantization}, lz4={self.use_lz4}")
    
    def compress_vectors(self, vectors: np.ndarray) -> Tuple[bytes, Dict]:
        """
        Compress vector array using configured techniques
        
        Args:
            vectors: numpy array of shape (n_vectors, dimension)
            
        Returns:
            Tuple of (compressed_bytes, metadata)
        """
        metadata = {
            'original_shape': vectors.shape,
            'original_dtype': str(vectors.dtype),
            'compression_steps': []
        }
        
        # Step 1: Precision reduction
        if self.precision != str(vectors.dtype):
            vectors = self._reduce_precision(vectors)
            metadata['compression_steps'].append(f'precision_{self.precision}')
        
        # Step 2: Quantization (if enabled and not already int8)
        if self.use_quantization and self.precision != 'int8':
            vectors = self._quantize_vectors(vectors)
            metadata['compression_steps'].append(f'quantization_{self.quantization_bits}bit')
        
        # Convert to bytes
        vector_bytes = vectors.tobytes()
        
        # Step 3: Lossless compression
        if self.use_lz4:
            vector_bytes = lz4.frame.compress(vector_bytes)
            metadata['compression_steps'].append('lz4')
        
        # Calculate compression ratio
        original_size = vectors.size * vectors.itemsize
        compression_ratio = len(vector_bytes) / original_size
        metadata['compression_ratio'] = compression_ratio
        metadata['compressed_size'] = len(vector_bytes)
        metadata['original_size'] = original_size
        
        logger.info(f"Vector compression completed: {compression_ratio:.2%} of original size")
        
        return vector_bytes, metadata
    
    def decompress_vectors(self, compressed_bytes: bytes, metadata: Dict) -> np.ndarray:
        """
        Decompress vector array back to original format
        
        Args:
            compressed_bytes: Compressed vector bytes
            metadata: Compression metadata
            
        Returns:
            Decompressed numpy array (float32)
        """
        # Step 1: Decompress if LZ4 was used
        if 'lz4' in metadata['compression_steps']:
            compressed_bytes = lz4.frame.decompress(compressed_bytes)
        
        # Step 2: Convert bytes back to numpy array
        original_shape = metadata['original_shape']
        
        # Determine the dtype after compression
        if 'precision_float16' in metadata['compression_steps']:
            dtype = np.float16
        elif 'precision_int8' in metadata['compression_steps'] or 'quantization' in str(metadata['compression_steps']):
            dtype = np.int8
        else:
            dtype = np.float32
        
        # Create array from bytes
        vectors = np.frombuffer(compressed_bytes, dtype=dtype)
        vectors = vectors.reshape(original_shape)
        
        # Step 3: Reverse quantization if needed
        if 'quantization' in str(metadata['compression_steps']):
            vectors = self._dequantize_vectors(vectors, metadata)
        
        # Step 4: Convert back to float32
        if dtype != np.float32:
            vectors = vectors.astype(np.float32)
        
        return vectors
    
    def _reduce_precision(self, vectors: np.ndarray) -> np.ndarray:
        """
        Reduce precision from float32 to float16 or int8
        
        Args:
            vectors: float32 numpy array
            
        Returns:
            Reduced precision array
        """
        if self.precision == 'float16':
            return vectors.astype(np.float16)
        elif self.precision == 'int8':
            # Normalize to -128 to 127 range
            min_val, max_val = vectors.min(), vectors.max()
            if max_val > min_val:
                normalized = (vectors - min_val) / (max_val - min_val) * 255 - 128
                return normalized.astype(np.int8)
            else:
                return np.zeros_like(vectors, dtype=np.int8)
        else:
            return vectors
    
    def _quantize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """
        Apply quantization to reduce precision further
        
        Args:
            vectors: numpy array
            
        Returns:
            Quantized array
        """
        if self.quantization_bits >= 8:
            return vectors
        
        # Scalar quantization
        levels = 2 ** self.quantization_bits
        
        if vectors.dtype == np.float32 or vectors.dtype == np.float16:
            # For floating point, quantize to discrete levels
            min_val, max_val = vectors.min(), vectors.max()
            scale = (max_val - min_val) / (levels - 1)
            
            if scale > 0:
                quantized = np.round((vectors - min_val) / scale) * scale + min_val
                return quantized.astype(vectors.dtype)
        
        return vectors
    
    def _dequantize_vectors(self, vectors: np.ndarray, metadata: Dict) -> np.ndarray:
        """
        Reverse quantization (simplified - full implementation would need quantization params)
        
        Args:
            vectors: Quantized array
            metadata: Compression metadata
            
        Returns:
            Dequantized array
        """
        # This is a simplified implementation
        # In practice, you'd store quantization parameters (min, max, scale)
        return vectors.astype(np.float32)
    
    def get_compression_stats(self, original_vectors: np.ndarray, compressed_bytes: bytes, metadata: Dict) -> Dict:
        """
        Get detailed compression statistics
        
        Args:
            original_vectors: Original uncompressed vectors
            compressed_bytes: Compressed bytes
            metadata: Compression metadata
            
        Returns:
            Statistics dictionary
        """
        original_size = original_vectors.nbytes
        compressed_size = len(compressed_bytes)
        
        # Calculate reconstruction error (simplified)
        decompressed = self.decompress_vectors(compressed_bytes, metadata)
        
        if original_vectors.shape == decompressed.shape:
            mse = np.mean((original_vectors - decompressed) ** 2)
            rmse = np.sqrt(mse)
        else:
            mse = rmse = float('inf')
        
        return {
            'original_size_bytes': original_size,
            'compressed_size_bytes': compressed_size,
            'compression_ratio': compressed_size / original_size,
            'space_saved_percent': (1 - compressed_size / original_size) * 100,
            'rmse': rmse,
            'techniques_used': metadata['compression_steps'],
            'precision': self.precision
        }