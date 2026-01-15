"""
Entity Tracker - Track Function/Class Mentions Across Sessions
Links code entities to session history
"""

import logging
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class EntityMention:
    """Record of an entity mention in a session"""
    
    def __init__(
        self,
        entity_name: str,
        session_id: str,
        turn_id: int,
        context: str,
        timestamp: Optional[str] = None
    ):
        self.entity_name = entity_name
        self.session_id = session_id
        self.turn_id = turn_id
        self.context = context  # Snippet of text where entity was mentioned
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity_name': self.entity_name,
            'session_id': self.session_id,
            'turn_id': self.turn_id,
            'context': self.context,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityMention':
        return cls(
            entity_name=data['entity_name'],
            session_id=data['session_id'],
            turn_id=data['turn_id'],
            context=data['context'],
            timestamp=data.get('timestamp')
        )


class EntityTracker:
    """
    Track mentions of code entities (functions/classes) across sessions
    
    Features:
    - Record when entities are mentioned
    - Find which sessions discussed an entity
    - Get context around entity mentions
    - Link entities to sessions
    """
    
    def __init__(self, code_index: Optional[Dict[str, Any]] = None, storage_dir: str = "data/code_index"):
        """
        Initialize entity tracker
        
        Args:
            code_index: Optional code index (from CodeIndexer)
            storage_dir: Directory to store tracking data
        """
        self.code_index = code_index or {'functions': {}, 'classes': {}}
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # entity_name -> [EntityMention]
        self.mentions: Dict[str, List[EntityMention]] = defaultdict(list)
        
        # session_id -> Set[entity_name]
        self.session_entities: Dict[str, Set[str]] = defaultdict(set)
        
        logger.info("EntityTracker initialized")
    
    def set_code_index(self, code_index: Dict[str, Any]) -> None:
        """Update the code index"""
        self.code_index = code_index
        logger.debug("Code index updated")
    
    def extract_entities_from_text(self, text: str) -> List[str]:
        """
        Extract entity names from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of entity names found
        """
        entities = []
        text_lower = text.lower()
        
        # Check functions
        for func_key, func_info in self.code_index.get('functions', {}).items():
            func_name = func_info.get('name', func_key.split('.')[-1])
            if func_name.lower() in text_lower:
                entities.append(func_name)
        
        # Check classes
        for class_key, class_info in self.code_index.get('classes', {}).items():
            class_name = class_info.get('name', class_key.split('.')[-1])
            if class_name.lower() in text_lower:
                entities.append(class_name)
        
        return list(set(entities))  # Deduplicate
    
    def record_mention(
        self,
        entity_name: str,
        session_id: str,
        turn_id: int,
        context: str
    ) -> None:
        """
        Record that an entity was mentioned
        
        Args:
            entity_name: Name of function/class
            session_id: Session where it was mentioned
            turn_id: Turn number in session
            context: Text context around the mention
        """
        mention = EntityMention(
            entity_name=entity_name,
            session_id=session_id,
            turn_id=turn_id,
            context=context[:200]  # Limit context length
        )
        
        self.mentions[entity_name].append(mention)
        self.session_entities[session_id].add(entity_name)
        
        logger.debug(f"Recorded mention: {entity_name} in session {session_id}")
    
    def record_turn(
        self,
        session_id: str,
        turn_id: int,
        query: str,
        response: str
    ) -> List[str]:
        """
        Analyze a turn and record entity mentions
        
        Args:
            session_id: Session identifier
            turn_id: Turn number
            query: User query
            response: Agent response
            
        Returns:
            List of entities found
        """
        # Combine query and response for analysis
        full_text = f"{query} {response}"
        
        # Extract entities
        entities = self.extract_entities_from_text(full_text)
        
        # Record each entity
        for entity in entities:
            # Get context (snippet around entity)
            entity_lower = entity.lower()
            text_lower = full_text.lower()
            idx = text_lower.find(entity_lower)
            
            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(full_text), idx + len(entity) + 50)
                context = full_text[start:end]
                
                self.record_mention(entity, session_id, turn_id, context)
        
        return entities
    
    def get_entity_history(self, entity_name: str) -> List[EntityMention]:
        """
        Get all mentions of an entity
        
        Args:
            entity_name: Entity to search for
            
        Returns:
            List of EntityMention objects
        """
        return self.mentions.get(entity_name, [])
    
    def get_sessions_for_entity(self, entity_name: str) -> List[str]:
        """
        Get all sessions that mentioned an entity
        
        Args:
            entity_name: Entity to search for
            
        Returns:
            List of session IDs
        """
        sessions = set()
        for mention in self.mentions.get(entity_name, []):
            sessions.add(mention.session_id)
        
        return sorted(sessions)
    
    def get_entities_for_session(self, session_id: str) -> List[str]:
        """
        Get all entities mentioned in a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of entity names
        """
        return sorted(self.session_entities.get(session_id, set()))
    
    def get_last_mention(self, entity_name: str) -> Optional[EntityMention]:
        """
        Get the most recent mention of an entity
        
        Args:
            entity_name: Entity to search for
            
        Returns:
            Most recent EntityMention or None
        """
        mentions = self.mentions.get(entity_name, [])
        if not mentions:
            return None
        
        # Sort by timestamp (most recent first)
        sorted_mentions = sorted(
            mentions,
            key=lambda m: m.timestamp,
            reverse=True
        )
        
        return sorted_mentions[0]
    
    def get_related_entities(self, entity_name: str, limit: int = 5) -> List[str]:
        """
        Get entities frequently mentioned together with this entity
        
        Args:
            entity_name: Entity to find related entities for
            limit: Maximum number of related entities to return
            
        Returns:
            List of related entity names
        """
        # Get sessions that mentioned this entity
        sessions = self.get_sessions_for_entity(entity_name)
        
        # Count co-occurrences
        co_occurrence: Dict[str, int] = defaultdict(int)
        
        for session_id in sessions:
            entities_in_session = self.get_entities_for_session(session_id)
            for other_entity in entities_in_session:
                if other_entity != entity_name:
                    co_occurrence[other_entity] += 1
        
        # Sort by frequency
        sorted_entities = sorted(
            co_occurrence.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [entity for entity, count in sorted_entities[:limit]]
    
    def search_mentions(self, keyword: str) -> Dict[str, List[EntityMention]]:
        """
        Search for keyword in mention contexts
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            Dict mapping entity names to matching mentions
        """
        keyword_lower = keyword.lower()
        results = {}
        
        for entity_name, mentions in self.mentions.items():
            matching = [
                m for m in mentions
                if keyword_lower in m.context.lower()
            ]
            if matching:
                results[entity_name] = matching
        
        return results
    
    def save(self) -> None:
        """Save tracking data to disk"""
        data = {
            'mentions': {
                entity: [m.to_dict() for m in mentions]
                for entity, mentions in self.mentions.items()
            },
            'session_entities': {
                session: list(entities)
                for session, entities in self.session_entities.items()
            }
        }
        
        tracking_file = self.storage_dir / 'entity_tracking.json'
        with open(tracking_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Entity tracking saved to {tracking_file}")
    
    def load(self) -> bool:
        """
        Load tracking data from disk
        
        Returns:
            True if loaded successfully
        """
        tracking_file = self.storage_dir / 'entity_tracking.json'
        
        if not tracking_file.exists():
            logger.debug("No tracking data found")
            return False
        
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore mentions
            self.mentions.clear()
            for entity, mentions_data in data.get('mentions', {}).items():
                self.mentions[entity] = [
                    EntityMention.from_dict(m) for m in mentions_data
                ]
            
            # Restore session entities
            self.session_entities.clear()
            for session, entities in data.get('session_entities', {}).items():
                self.session_entities[session] = set(entities)
            
            logger.info(
                f"Entity tracking loaded: {len(self.mentions)} entities tracked"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error loading tracking data: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracking statistics"""
        total_mentions = sum(len(mentions) for mentions in self.mentions.values())
        
        return {
            'total_entities_tracked': len(self.mentions),
            'total_mentions': total_mentions,
            'total_sessions': len(self.session_entities),
            'avg_mentions_per_entity': total_mentions / len(self.mentions) if self.mentions else 0
        }
