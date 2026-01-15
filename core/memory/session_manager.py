"""
Session Manager - Multi-Session Coordination for MCP v6
Manages multiple sessions, persistence, and lifecycle
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
import logging
from datetime import datetime

from memory.trimming_session import TrimmingSession
from memory.summarizing_session import SummarizingSession
from storage.session_storage import SessionStorage


logger = logging.getLogger(__name__)


class SessionType(Enum):
    """Types of development sessions"""
    FEATURE_IMPLEMENTATION = "feature"
    BUG_FIXING = "bugfix"
    CODE_REVIEW = "review"
    REFACTORING = "refactor"
    GENERAL = "general"


class SessionStrategy(Enum):
    """Session memory strategies"""
    TRIMMING = "trimming"
    SUMMARIZING = "summarizing"


class SessionManager:
    """
    Manages multiple sessions with persistence
    
    Features:
    - Create/load/save/delete sessions
    - Support for both Trimming and Summarizing strategies
    - Automatic persistence to disk
    - Session lifecycle management
    - Cross-session queries
    """
    
    def __init__(
        self,
        storage: Optional[SessionStorage] = None,
        default_strategy: SessionStrategy = SessionStrategy.TRIMMING,
        auto_save: bool = True
    ):
        """
        Initialize session manager
        
        Args:
            storage: SessionStorage instance (creates default if None)
            default_strategy: Default session strategy
            auto_save: Automatically save sessions after each turn
        """
        self.storage = storage or SessionStorage()
        self.default_strategy = default_strategy
        self.auto_save = auto_save
        
        # Active sessions in memory
        self.active_sessions: Dict[str, Union[TrimmingSession, SummarizingSession]] = {}
        
        logger.info(f"SessionManager initialized (strategy={default_strategy.value}, auto_save={auto_save})")
    
    async def create_session(
        self,
        session_id: str,
        session_type: SessionType = SessionType.GENERAL,
        strategy: Optional[SessionStrategy] = None,
        **kwargs
    ) -> Union[TrimmingSession, SummarizingSession]:
        """
        Create a new session
        
        Args:
            session_id: Unique session identifier
            session_type: Type of session
            strategy: Session strategy (uses default if None)
            **kwargs: Additional arguments for session constructor
            
        Returns:
            Created session instance
        """
        if session_id in self.active_sessions:
            logger.warning(f"Session {session_id} already exists, returning existing")
            return self.active_sessions[session_id]
        
        strategy = strategy or self.default_strategy
        
        # Create session based on strategy
        if strategy == SessionStrategy.TRIMMING:
            session = TrimmingSession(
                session_id=session_id,
                session_type=session_type.value,
                max_turns=kwargs.get('max_turns', 8)
            )
        else:  # SUMMARIZING
            session = SummarizingSession(
                session_id=session_id,
                session_type=session_type.value,
                keep_last_n_turns=kwargs.get('keep_last_n_turns', 3),
                context_limit=kwargs.get('context_limit', 10)
            )
        
        self.active_sessions[session_id] = session
        
        # Save metadata
        metadata = {
            'session_id': session_id,
            'session_type': session_type.value,
            'strategy': strategy.value,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        await self.storage.save_metadata(session_id, metadata)
        
        logger.info(f"Session created: {session_id} (type={session_type.value}, strategy={strategy.value})")
        return session
    
    async def load_session(self, session_id: str) -> Optional[Union[TrimmingSession, SummarizingSession]]:
        """
        Load a session from storage
        
        Args:
            session_id: Session identifier
            
        Returns:
            Loaded session or None if not found
        """
        # Check if already in memory
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Load from storage
        metadata = await self.storage.load_metadata(session_id)
        if not metadata:
            logger.warning(f"Session {session_id} not found in storage")
            return None
        
        turns = await self.storage.load_session(session_id)
        
        # Reconstruct session based on strategy
        strategy = SessionStrategy(metadata.get('strategy', 'trimming'))
        
        if strategy == SessionStrategy.TRIMMING:
            session = TrimmingSession(
                session_id=session_id,
                session_type=metadata.get('session_type', 'general')
            )
        else:
            session = SummarizingSession(
                session_id=session_id,
                session_type=metadata.get('session_type', 'general')
            )
        
        # Restore turns
        for turn in turns:
            session.add_turn(
                query=turn.get('query', ''),
                response=turn.get('response', ''),
                metadata=turn.get('metadata', {})
            )
        
        self.active_sessions[session_id] = session
        logger.info(f"Session loaded: {session_id} ({len(turns)} turns)")
        
        return session
    
    async def save_session(self, session_id: str) -> bool:
        """
        Save a session to storage
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if saved successfully
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not in active sessions")
            return False
        
        session = self.active_sessions[session_id]
        session_data = session.to_dict()
        
        # Save each turn
        for turn in session_data.get('turns', []):
            await self.storage.save_turn(session_id, turn)
        
        # Update metadata
        metadata = await self.storage.load_metadata(session_id)
        if metadata:
            metadata['last_saved'] = datetime.now().isoformat()
            metadata['turn_count'] = len(session_data.get('turns', []))
            await self.storage.save_metadata(session_id, metadata)
        
        logger.debug(f"Session saved: {session_id}")
        return True
    
    async def add_turn_to_session(
        self,
        session_id: str,
        query: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a turn to a session
        
        Args:
            session_id: Session identifier
            query: User query
            response: Agent response
            metadata: Optional metadata
            
        Returns:
            True if added successfully
        """
        # Load session if not in memory
        session = await self.load_session(session_id)
        if not session:
            logger.error(f"Cannot add turn: session {session_id} not found")
            return False
        
        # Add turn
        session.add_turn(query, response, metadata)
        
        # Auto-save if enabled
        if self.auto_save:
            turn_data = {
                'query': query,
                'response': response,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
            await self.storage.save_turn(session_id, turn_data)
        
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Delete from storage
        deleted = await self.storage.delete_session(session_id)
        
        if deleted:
            logger.info(f"Session deleted: {session_id}")
        
        return deleted
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions
        
        Returns:
            List of session summaries
        """
        session_ids = await self.storage.list_sessions()
        summaries = []
        
        for session_id in session_ids:
            summary = await self.storage.get_session_summary(session_id)
            if summary:
                summaries.append(summary)
        
        return summaries
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary of a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary dict
        """
        # Try active session first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id].get_summary()
        
        # Load from storage
        return await self.storage.get_session_summary(session_id)
    
    async def get_session_context(self, session_id: str) -> Optional[str]:
        """
        Get formatted context window for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Formatted context string or None
        """
        session = await self.load_session(session_id)
        if not session:
            return None
        
        return session.get_context_window()
    
    async def search_across_sessions(self, keyword: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for keyword across all sessions
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            Dict mapping session_id to matching turns
        """
        results = {}
        session_ids = await self.storage.list_sessions()
        
        for session_id in session_ids:
            session = await self.load_session(session_id)
            if session:
                if isinstance(session, TrimmingSession):
                    matches = session.search_in_history(keyword)
                    if matches:
                        results[session_id] = matches
                elif isinstance(session, SummarizingSession):
                    search_result = session.search_in_history(keyword)
                    if search_result['in_summary'] or search_result['matching_turns']:
                        results[session_id] = search_result['matching_turns']
        
        return results
    
    async def cleanup_old_sessions(self) -> int:
        """
        Clean up old sessions based on retention policy
        
        Returns:
            Number of sessions deleted
        """
        return await self.storage.cleanup_old_sessions()
    
    def get_active_session_count(self) -> int:
        """Get number of active sessions in memory"""
        return len(self.active_sessions)
    
    async def close_session(self, session_id: str) -> bool:
        """
        Close a session (save and remove from memory)
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if closed successfully
        """
        if session_id not in self.active_sessions:
            return False
        
        # Save before closing
        await self.save_session(session_id)
        
        # Update metadata
        metadata = await self.storage.load_metadata(session_id)
        if metadata:
            metadata['status'] = 'closed'
            metadata['closed_at'] = datetime.now().isoformat()
            await self.storage.save_metadata(session_id, metadata)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        logger.info(f"Session closed: {session_id}")
        return True
