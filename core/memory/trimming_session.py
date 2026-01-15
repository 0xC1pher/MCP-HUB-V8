"""
Trimming Session - Keep Last N Turns Strategy
Simple session memory that maintains only the most recent turns
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TrimmingSession:
    """
    Session memory that keeps only the last N turns
    
    Strategy:
    - Maintains a sliding window of recent turns
    - Oldest turns are discarded when limit is reached
    - No compression, just simple truncation
    - Fast and predictable memory usage
    
    Use Cases:
    - Bug fixing sessions (recent context is most important)
    - Quick feature implementations
    - Short-lived development tasks
    """
    
    def __init__(self, session_id: str, max_turns: int = 8, session_type: str = "general"):
        """
        Initialize trimming session
        
        Args:
            session_id: Unique session identifier
            max_turns: Maximum number of turns to keep
            session_type: Type of session (feature, bugfix, review, refactor, general)
        """
        self.session_id = session_id
        self.max_turns = max_turns
        self.session_type = session_type
        self.turns: List[Dict[str, Any]] = []
        self.created_at = datetime.now().isoformat()
        self.entities_mentioned: List[str] = []  # Track mentioned functions/classes
        
        logger.info(f"TrimmingSession created: {session_id} (max_turns={max_turns}, type={session_type})")
    
    def add_turn(self, query: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a new turn to the session
        
        Args:
            query: User query/input
            response: Agent response/output
            metadata: Optional metadata (entities, files, etc.)
        """
        turn = {
            'turn_id': len(self.turns) + 1,
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'metadata': metadata or {}
        }
        
        self.turns.append(turn)
        
        # Extract entities if present in metadata
        if metadata and 'entities' in metadata:
            for entity in metadata['entities']:
                if entity not in self.entities_mentioned:
                    self.entities_mentioned.append(entity)
        
        # Trim if exceeds max_turns
        if len(self.turns) > self.max_turns:
            removed = self.turns.pop(0)
            logger.debug(f"Trimmed turn {removed['turn_id']} from session {self.session_id}")
        
        logger.debug(f"Turn added to session {self.session_id} (total: {len(self.turns)})")
    
    def get_recent_turns(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the N most recent turns
        
        Args:
            n: Number of turns to retrieve (None = all)
            
        Returns:
            List of turn dictionaries
        """
        if n is None:
            return self.turns.copy()
        
        return self.turns[-n:] if n > 0 else []
    
    def get_context_window(self) -> str:
        """
        Get formatted context window for LLM
        
        Returns:
            Formatted string with recent conversation history
        """
        if not self.turns:
            return ""
        
        context_parts = [f"Session: {self.session_id} (Type: {self.session_type})"]
        context_parts.append(f"Recent conversation ({len(self.turns)} turns):\n")
        
        for turn in self.turns:
            context_parts.append(f"Turn {turn['turn_id']}:")
            context_parts.append(f"User: {turn['query']}")
            context_parts.append(f"Assistant: {turn['response'][:200]}...")  # Truncate long responses
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_entities_mentioned(self) -> List[str]:
        """
        Get all entities (functions/classes) mentioned in this session
        
        Returns:
            List of entity names
        """
        return self.entities_mentioned.copy()
    
    def search_in_history(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search for keyword in session history
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            List of turns containing the keyword
        """
        keyword_lower = keyword.lower()
        matching_turns = []
        
        for turn in self.turns:
            if (keyword_lower in turn['query'].lower() or 
                keyword_lower in turn['response'].lower()):
                matching_turns.append(turn)
        
        return matching_turns
    
    def get_last_mention_of_entity(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        Find the last turn where an entity was mentioned
        
        Args:
            entity_name: Name of function/class to search for
            
        Returns:
            Turn dict or None if not found
        """
        entity_lower = entity_name.lower()
        
        # Search backwards (most recent first)
        for turn in reversed(self.turns):
            if (entity_lower in turn['query'].lower() or 
                entity_lower in turn['response'].lower()):
                return turn
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize session to dictionary
        
        Returns:
            Session data as dict
        """
        return {
            'session_id': self.session_id,
            'session_type': self.session_type,
            'max_turns': self.max_turns,
            'created_at': self.created_at,
            'turn_count': len(self.turns),
            'entities_mentioned': self.entities_mentioned,
            'turns': self.turns
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrimmingSession':
        """
        Deserialize session from dictionary
        
        Args:
            data: Session data dict
            
        Returns:
            TrimmingSession instance
        """
        session = cls(
            session_id=data['session_id'],
            max_turns=data.get('max_turns', 8),
            session_type=data.get('session_type', 'general')
        )
        
        session.created_at = data.get('created_at', session.created_at)
        session.entities_mentioned = data.get('entities_mentioned', [])
        session.turns = data.get('turns', [])
        
        return session
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get session summary
        
        Returns:
            Summary dict with key metrics
        """
        return {
            'session_id': self.session_id,
            'session_type': self.session_type,
            'created_at': self.created_at,
            'turn_count': len(self.turns),
            'max_turns': self.max_turns,
            'entities_mentioned_count': len(self.entities_mentioned),
            'entities': self.entities_mentioned[:10],  # Top 10
            'oldest_turn': self.turns[0]['timestamp'] if self.turns else None,
            'newest_turn': self.turns[-1]['timestamp'] if self.turns else None
        }
    
    def clear(self) -> None:
        """Clear all turns from session"""
        self.turns.clear()
        self.entities_mentioned.clear()
        logger.info(f"Session {self.session_id} cleared")
