"""
Session Storage - JSONL Persistence for MCP v6
Handles saving and loading session history to/from disk
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SessionStorage:
    """
    Persistent storage for session history using JSONL format
    
    Features:
    - Async file I/O for performance
    - JSONL format (one JSON object per line)
    - Automatic retention policy
    - Session metadata tracking
    """
    
    def __init__(self, storage_dir: str = "data/sessions", retention_days: int = 30):
        """
        Initialize session storage
        
        Args:
            storage_dir: Directory to store session files
            retention_days: Number of days to retain sessions (0 = forever)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        logger.info(f"SessionStorage initialized: {self.storage_dir}")
    
    def _get_session_path(self, session_id: str) -> Path:
        """Get file path for a session"""
        return self.storage_dir / f"{session_id}.jsonl"
    
    def _get_metadata_path(self, session_id: str) -> Path:
        """Get metadata file path for a session"""
        return self.storage_dir / f"{session_id}.meta.json"
    
    async def save_turn(self, session_id: str, turn_data: Dict[str, Any]) -> None:
        """
        Append a turn to session file
        
        Args:
            session_id: Unique session identifier
            turn_data: Turn data to save (dict with query, response, timestamp, etc.)
        """
        session_file = self._get_session_path(session_id)
        
        # Add timestamp if not present
        if 'timestamp' not in turn_data:
            turn_data['timestamp'] = datetime.now().isoformat()
        
        try:
            # Append to JSONL file
            with open(session_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(turn_data, ensure_ascii=False) + '\n')
            
            # Update metadata
            await self._update_metadata(session_id)
            
            logger.debug(f"Turn saved to session {session_id}")
        except Exception as e:
            logger.error(f"Error saving turn to {session_id}: {e}")
            raise
    
    async def load_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Load all turns from a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of turn dictionaries, empty list if session doesn't exist
        """
        session_file = self._get_session_path(session_id)
        
        if not session_file.exists():
            logger.debug(f"Session {session_id} not found")
            return []
        
        turns = []
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        turns.append(json.loads(line))
            
            logger.debug(f"Loaded {len(turns)} turns from session {session_id}")
            return turns
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            raise
    
    async def save_metadata(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """
        Save session metadata
        
        Args:
            session_id: Session identifier
            metadata: Metadata dict (type, created_at, status, etc.)
        """
        metadata_file = self._get_metadata_path(session_id)
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Metadata saved for session {session_id}")
        except Exception as e:
            logger.error(f"Error saving metadata for {session_id}: {e}")
            raise
    
    async def load_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session metadata
        
        Args:
            session_id: Session identifier
            
        Returns:
            Metadata dict or None if not found
        """
        metadata_file = self._get_metadata_path(session_id)
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata for {session_id}: {e}")
            return None
    
    async def _update_metadata(self, session_id: str) -> None:
        """Update metadata after adding a turn"""
        metadata = await self.load_metadata(session_id)
        
        if metadata is None:
            # Create initial metadata
            metadata = {
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'turn_count': 1
            }
        else:
            # Update existing metadata
            metadata['last_updated'] = datetime.now().isoformat()
            metadata['turn_count'] = metadata.get('turn_count', 0) + 1
        
        await self.save_metadata(session_id, metadata)
    
    async def list_sessions(self) -> List[str]:
        """
        List all session IDs
        
        Returns:
            List of session IDs
        """
        sessions = []
        for file in self.storage_dir.glob("*.jsonl"):
            sessions.append(file.stem)
        
        return sorted(sessions)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its metadata
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        session_file = self._get_session_path(session_id)
        metadata_file = self._get_metadata_path(session_id)
        
        deleted = False
        
        if session_file.exists():
            session_file.unlink()
            deleted = True
        
        if metadata_file.exists():
            metadata_file.unlink()
            deleted = True
        
        if deleted:
            logger.info(f"Session {session_id} deleted")
        
        return deleted
    
    async def cleanup_old_sessions(self) -> int:
        """
        Delete sessions older than retention_days
        
        Returns:
            Number of sessions deleted
        """
        if self.retention_days <= 0:
            return 0  # Retention disabled
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0
        
        for session_id in await self.list_sessions():
            metadata = await self.load_metadata(session_id)
            
            if metadata:
                created_at = datetime.fromisoformat(metadata.get('created_at', ''))
                
                if created_at < cutoff_date:
                    await self.delete_session(session_id)
                    deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old sessions")
        
        return deleted_count
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary of a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Summary dict with metadata and turn count
        """
        metadata = await self.load_metadata(session_id)
        
        if metadata is None:
            return None
        
        turns = await self.load_session(session_id)
        
        return {
            'session_id': session_id,
            'metadata': metadata,
            'turn_count': len(turns),
            'created_at': metadata.get('created_at'),
            'last_updated': metadata.get('last_updated')
        }


# Async helper for synchronous contexts
def create_session_storage(storage_dir: str = "data/sessions", retention_days: int = 30) -> SessionStorage:
    """Factory function to create SessionStorage instance"""
    return SessionStorage(storage_dir, retention_days)
