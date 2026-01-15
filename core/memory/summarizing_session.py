"""
Summarizing Session - Compress Old + Keep Recent Strategy
Advanced session memory with intelligent summarization
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SummarizingSession:
    """
    Session memory that compresses old turns and keeps recent ones verbatim
    
    Strategy:
    - Keeps last N turns verbatim (recent context)
    - Compresses older turns into a summary
    - Summary updated periodically
    - Balances context retention with memory efficiency
    
    Use Cases:
    - Long feature implementation sessions
    - Complex refactoring tasks
    - Multi-day development workflows
    """
    
    def __init__(
        self,
        session_id: str,
        keep_last_n_turns: int = 3,
        context_limit: int = 10,
        session_type: str = "general",
        summarizer: Optional[Callable[[List[Dict]], str]] = None
    ):
        """
        Initialize summarizing session
        
        Args:
            session_id: Unique session identifier
            keep_last_n_turns: Number of recent turns to keep verbatim
            context_limit: Maximum total turns before triggering summarization
            session_type: Type of session (feature, bugfix, review, refactor, general)
            summarizer: Optional custom summarization function
        """
        self.session_id = session_id
        self.keep_last_n_turns = keep_last_n_turns
        self.context_limit = context_limit
        self.session_type = session_type
        self.summarizer = summarizer or self._default_summarizer
        
        self.summary: str = ""
        self.summary_turn_count: int = 0  # How many turns are in the summary
        self.recent_turns: List[Dict[str, Any]] = []
        self.created_at = datetime.now().isoformat()
        self.last_summarized_at: Optional[str] = None
        self.entities_mentioned: List[str] = []
        
        logger.info(
            f"SummarizingSession created: {session_id} "
            f"(keep={keep_last_n_turns}, limit={context_limit}, type={session_type})"
        )
    
    def add_turn(self, query: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a new turn to the session
        
        Args:
            query: User query/input
            response: Agent response/output
            metadata: Optional metadata (entities, files, etc.)
        """
        turn = {
            'turn_id': self.summary_turn_count + len(self.recent_turns) + 1,
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'metadata': metadata or {}
        }
        
        self.recent_turns.append(turn)
        
        # Extract entities
        if metadata and 'entities' in metadata:
            for entity in metadata['entities']:
                if entity not in self.entities_mentioned:
                    self.entities_mentioned.append(entity)
        
        # Check if we need to summarize
        if len(self.recent_turns) > self.context_limit:
            self._trigger_summarization()
        
        logger.debug(
            f"Turn added to session {self.session_id} "
            f"(recent: {len(self.recent_turns)}, summarized: {self.summary_turn_count})"
        )
    
    def _trigger_summarization(self) -> None:
        """Compress old turns into summary, keep recent ones"""
        if len(self.recent_turns) <= self.keep_last_n_turns:
            return  # Nothing to summarize
        
        # Split turns into "to summarize" and "to keep"
        turns_to_summarize = self.recent_turns[:-self.keep_last_n_turns]
        turns_to_keep = self.recent_turns[-self.keep_last_n_turns:]
        
        # Generate new summary
        new_summary_part = self.summarizer(turns_to_summarize)
        
        # Append to existing summary
        if self.summary:
            self.summary += f"\n\n--- Additional Context ---\n{new_summary_part}"
        else:
            self.summary = new_summary_part
        
        # Update counts
        self.summary_turn_count += len(turns_to_summarize)
        self.recent_turns = turns_to_keep
        self.last_summarized_at = datetime.now().isoformat()
        
        logger.info(
            f"Session {self.session_id} summarized: "
            f"{len(turns_to_summarize)} turns compressed, {len(turns_to_keep)} kept"
        )
    
    def _default_summarizer(self, turns: List[Dict[str, Any]]) -> str:
        """
        Default summarization strategy (rule-based)
        
        Args:
            turns: List of turns to summarize
            
        Returns:
            Summary string
        """
        if not turns:
            return ""
        
        # Extract key information
        queries = [t['query'] for t in turns]
        entities = set()
        files_mentioned = set()
        
        for turn in turns:
            metadata = turn.get('metadata', {})
            if 'entities' in metadata:
                entities.update(metadata['entities'])
            if 'files' in metadata:
                files_mentioned.update(metadata['files'])
        
        # Build summary
        summary_parts = [
            f"Summary of {len(turns)} turns (Turn {turns[0]['turn_id']} to {turns[-1]['turn_id']}):",
            f"Session Type: {self.session_type}",
            f"Time Range: {turns[0]['timestamp']} to {turns[-1]['timestamp']}",
        ]
        
        if entities:
            summary_parts.append(f"Entities Discussed: {', '.join(sorted(entities)[:10])}")
        
        if files_mentioned:
            summary_parts.append(f"Files Modified: {', '.join(sorted(files_mentioned)[:5])}")
        
        # Add key queries
        summary_parts.append("\nKey Activities:")
        for i, query in enumerate(queries[:5], 1):  # Top 5 queries
            summary_parts.append(f"  {i}. {query[:100]}...")
        
        return "\n".join(summary_parts)
    
    def get_context_window(self) -> str:
        """
        Get formatted context window for LLM
        
        Returns:
            Formatted string with summary + recent turns
        """
        context_parts = [f"Session: {self.session_id} (Type: {self.session_type})"]
        
        # Add summary if exists
        if self.summary:
            context_parts.append("\n=== Previous Context (Summarized) ===")
            context_parts.append(self.summary)
            context_parts.append(f"({self.summary_turn_count} turns summarized)")
        
        # Add recent turns
        if self.recent_turns:
            context_parts.append("\n=== Recent Conversation ===")
            for turn in self.recent_turns:
                context_parts.append(f"\nTurn {turn['turn_id']}:")
                context_parts.append(f"User: {turn['query']}")
                context_parts.append(f"Assistant: {turn['response'][:300]}...")
        
        return "\n".join(context_parts)
    
    def get_recent_turns(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the N most recent turns (verbatim)
        
        Args:
            n: Number of turns to retrieve (None = all recent)
            
        Returns:
            List of turn dictionaries
        """
        if n is None:
            return self.recent_turns.copy()
        
        return self.recent_turns[-n:] if n > 0 else []
    
    def get_full_summary(self) -> str:
        """Get the compressed summary of old turns"""
        return self.summary
    
    def search_in_history(self, keyword: str) -> Dict[str, Any]:
        """
        Search for keyword in both summary and recent turns
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            Dict with 'in_summary' (bool) and 'matching_turns' (list)
        """
        keyword_lower = keyword.lower()
        
        # Search in summary
        in_summary = keyword_lower in self.summary.lower() if self.summary else False
        
        # Search in recent turns
        matching_turns = []
        for turn in self.recent_turns:
            if (keyword_lower in turn['query'].lower() or 
                keyword_lower in turn['response'].lower()):
                matching_turns.append(turn)
        
        return {
            'in_summary': in_summary,
            'matching_turns': matching_turns
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize session to dictionary
        
        Returns:
            Session data as dict
        """
        return {
            'session_id': self.session_id,
            'session_type': self.session_type,
            'keep_last_n_turns': self.keep_last_n_turns,
            'context_limit': self.context_limit,
            'created_at': self.created_at,
            'last_summarized_at': self.last_summarized_at,
            'summary': self.summary,
            'summary_turn_count': self.summary_turn_count,
            'recent_turns': self.recent_turns,
            'entities_mentioned': self.entities_mentioned
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SummarizingSession':
        """
        Deserialize session from dictionary
        
        Args:
            data: Session data dict
            
        Returns:
            SummarizingSession instance
        """
        session = cls(
            session_id=data['session_id'],
            keep_last_n_turns=data.get('keep_last_n_turns', 3),
            context_limit=data.get('context_limit', 10),
            session_type=data.get('session_type', 'general')
        )
        
        session.created_at = data.get('created_at', session.created_at)
        session.last_summarized_at = data.get('last_summarized_at')
        session.summary = data.get('summary', '')
        session.summary_turn_count = data.get('summary_turn_count', 0)
        session.recent_turns = data.get('recent_turns', [])
        session.entities_mentioned = data.get('entities_mentioned', [])
        
        return session
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get session summary
        
        Returns:
            Summary dict with key metrics
        """
        total_turns = self.summary_turn_count + len(self.recent_turns)
        
        return {
            'session_id': self.session_id,
            'session_type': self.session_type,
            'created_at': self.created_at,
            'last_summarized_at': self.last_summarized_at,
            'total_turns': total_turns,
            'summarized_turns': self.summary_turn_count,
            'recent_turns': len(self.recent_turns),
            'entities_mentioned_count': len(self.entities_mentioned),
            'entities': self.entities_mentioned[:10],
            'has_summary': bool(self.summary)
        }
    
    def force_summarize(self) -> None:
        """Manually trigger summarization"""
        self._trigger_summarization()
