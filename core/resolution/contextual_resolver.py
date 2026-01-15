"""
Contextual Resolver - Resolve References to Concrete Entities
Combines session history, entity tracking, and reference detection
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .reference_detector import ReferenceDetector, Reference, ReferenceType

logger = logging.getLogger(__name__)


class ResolvedReference:
    """A reference that has been resolved to a concrete entity"""
    
    def __init__(
        self,
        original_text: str,
        resolved_entity: str,
        confidence: float,
        source: str,  # Where it was resolved from (e.g., "session_history", "entity_tracker")
        context: Optional[str] = None
    ):
        self.original_text = original_text
        self.resolved_entity = resolved_entity
        self.confidence = confidence
        self.source = source
        self.context = context
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_text': self.original_text,
            'resolved_entity': self.resolved_entity,
            'confidence': self.confidence,
            'source': self.source,
            'context': self.context
        }


class ContextualResolver:
    """
    Resolve contextual references using session history and entity tracking
    
    Strategy:
    1. Detect references in query
    2. Look up recent session history
    3. Find mentioned entities
    4. Match references to entities
    5. Expand query with concrete names
    """
    
    def __init__(
        self,
        reference_detector: Optional[ReferenceDetector] = None
    ):
        """
        Initialize contextual resolver
        
        Args:
            reference_detector: ReferenceDetector instance (creates default if None)
        """
        self.detector = reference_detector or ReferenceDetector()
        logger.info("ContextualResolver initialized")
    
    async def resolve_query(
        self,
        query: str,
        session_history: List[Dict[str, Any]],
        entity_tracker: Optional[Any] = None,
        code_index: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[ResolvedReference]]:
        """
        Resolve references in a query
        
        Args:
            query: User query with potential references
            session_history: Recent turns from session
            entity_tracker: EntityTracker instance (optional)
            code_index: Code index from CodeIndexer (optional)
            
        Returns:
            Tuple of (expanded_query, list of resolved references)
        """
        # Detect references
        references = self.detector.detect(query)
        
        if not references:
            logger.debug("No references detected in query")
            return query, []
        
        logger.debug(f"Resolving {len(references)} references")
        
        # Extract entities from session history
        session_entities = self._extract_entities_from_history(session_history)
        
        # Resolve each reference
        resolved_refs = []
        expanded_query = query
        
        for ref in references:
            resolved = await self._resolve_reference(
                ref,
                session_entities,
                entity_tracker,
                code_index
            )
            
            if resolved:
                resolved_refs.append(resolved)
                # Replace reference in query
                expanded_query = expanded_query.replace(
                    ref.text,
                    resolved.resolved_entity
                )
        
        logger.info(f"Resolved {len(resolved_refs)}/{len(references)} references")
        return expanded_query, resolved_refs
    
    def _extract_entities_from_history(
        self,
        session_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract entities mentioned in session history
        
        Args:
            session_history: List of turn dictionaries
            
        Returns:
            List of entity dicts with name, turn_id, context
        """
        entities = []
        
        for turn in session_history:
            turn_id = turn.get('turn_id', 0)
            query = turn.get('query', '')
            response = turn.get('response', '')
            metadata = turn.get('metadata', {})
            
            # Get entities from metadata if available
            if 'entities' in metadata:
                for entity_name in metadata['entities']:
                    entities.append({
                        'name': entity_name,
                        'turn_id': turn_id,
                        'context': query + ' ' + response,
                        'timestamp': turn.get('timestamp', '')
                    })
            
            # Simple extraction: look for common patterns
            # (This is basic; entity_tracker does better)
            full_text = query + ' ' + response
            words = full_text.split()
            
            for i, word in enumerate(words):
                # Look for function-like patterns (e.g., "process_payment")
                if '_' in word and word.replace('_', '').isalnum():
                    entities.append({
                        'name': word,
                        'turn_id': turn_id,
                        'context': ' '.join(words[max(0, i-5):min(len(words), i+6)]),
                        'timestamp': turn.get('timestamp', '')
                    })
        
        return entities
    
    async def _resolve_reference(
        self,
        reference: Reference,
        session_entities: List[Dict[str, Any]],
        entity_tracker: Optional[Any],
        code_index: Optional[Dict[str, Any]]
    ) -> Optional[ResolvedReference]:
        """
        Resolve a single reference
        
        Args:
            reference: Reference to resolve
            session_entities: Entities from session history
            entity_tracker: EntityTracker instance
            code_index: Code index
            
        Returns:
            ResolvedReference or None if couldn't resolve
        """
        # Extract entity type from reference
        entity_type = self.detector.extract_entity_type(reference.text)
        
        if not entity_type:
            logger.debug(f"Could not extract entity type from: {reference.text}")
            return None
        
        # Strategy 1: Look in recent session history (highest priority)
        if reference.ref_type in [ReferenceType.DEMONSTRATIVE, ReferenceType.PREVIOUS]:
            resolved = self._resolve_from_history(
                reference,
                entity_type,
                session_entities
            )
            if resolved:
                return resolved
        
        # Strategy 2: Use entity tracker
        if entity_tracker:
            resolved = self._resolve_from_tracker(
                reference,
                entity_type,
                entity_tracker
            )
            if resolved:
                return resolved
        
        # Strategy 3: Use code index (if only one match)
        if code_index:
            resolved = self._resolve_from_code_index(
                reference,
                entity_type,
                code_index
            )
            if resolved:
                return resolved
        
        logger.debug(f"Could not resolve reference: {reference.text}")
        return None
    
    def _resolve_from_history(
        self,
        reference: Reference,
        entity_type: str,
        session_entities: List[Dict[str, Any]]
    ) -> Optional[ResolvedReference]:
        """Resolve reference from session history"""
        
        # Filter entities by type (simple heuristic)
        type_keywords = {
            'function': ['function', 'método', 'def'],
            'class': ['class', 'clase'],
            'bug': ['bug', 'error', 'issue'],
            'file': ['file', 'archivo', '.py', '.js']
        }
        
        relevant_entities = []
        keywords = type_keywords.get(entity_type, [])
        
        for entity in session_entities:
            # Check if entity context mentions the type
            context_lower = entity['context'].lower()
            if any(kw in context_lower for kw in keywords):
                relevant_entities.append(entity)
        
        if not relevant_entities:
            relevant_entities = session_entities  # Fallback to all
        
        if not relevant_entities:
            return None
        
        # For "previous/last", get the most recent
        if reference.ref_type == ReferenceType.PREVIOUS:
            # Sort by turn_id (most recent first)
            sorted_entities = sorted(
                relevant_entities,
                key=lambda e: e['turn_id'],
                reverse=True
            )
            entity = sorted_entities[0]
        else:
            # For demonstratives, get the most recent
            sorted_entities = sorted(
                relevant_entities,
                key=lambda e: e['turn_id'],
                reverse=True
            )
            entity = sorted_entities[0]
        
        return ResolvedReference(
            original_text=reference.text,
            resolved_entity=entity['name'],
            confidence=reference.confidence * 0.9,  # High confidence from history
            source='session_history',
            context=entity['context'][:100]
        )
    
    def _resolve_from_tracker(
        self,
        reference: Reference,
        entity_type: str,
        entity_tracker: Any
    ) -> Optional[ResolvedReference]:
        """Resolve reference from entity tracker"""
        
        # Get last mentioned entity of this type
        # (This is simplified; real implementation would filter by type)
        
        # For now, just get the most recent mention
        # In a full implementation, we'd filter by entity_type
        
        # This is a placeholder - entity_tracker needs to support this
        logger.debug("Entity tracker resolution not fully implemented")
        return None
    
    def _resolve_from_code_index(
        self,
        reference: Reference,
        entity_type: str,
        code_index: Dict[str, Any]
    ) -> Optional[ResolvedReference]:
        """Resolve reference from code index (if unambiguous)"""
        
        # Map entity types to code index keys
        type_mapping = {
            'function': 'functions',
            'class': 'classes',
            'method': 'functions'
        }
        
        index_key = type_mapping.get(entity_type)
        if not index_key:
            return None
        
        entities = code_index.get(index_key, {})
        
        # Only resolve if there's exactly one match (unambiguous)
        if len(entities) == 1:
            entity_name = list(entities.keys())[0]
            return ResolvedReference(
                original_text=reference.text,
                resolved_entity=entity_name,
                confidence=reference.confidence * 0.5,  # Lower confidence
                source='code_index',
                context='Only one entity of this type in codebase'
            )
        
        return None
    
    def expand_query_with_context(
        self,
        query: str,
        resolved_refs: List[ResolvedReference]
    ) -> str:
        """
        Create an expanded query with resolved references
        
        Args:
            query: Original query
            resolved_refs: List of resolved references
            
        Returns:
            Expanded query string
        """
        if not resolved_refs:
            return query
        
        # Build context string
        context_parts = [query]
        context_parts.append("\n[Resolved References:]")
        
        for ref in resolved_refs:
            context_parts.append(
                f"- '{ref.original_text}' → {ref.resolved_entity} "
                f"(confidence: {ref.confidence:.2f}, source: {ref.source})"
            )
        
        return "\n".join(context_parts)
    
    def get_resolution_summary(
        self,
        query: str,
        resolved_refs: List[ResolvedReference]
    ) -> Dict[str, Any]:
        """
        Get summary of resolution process
        
        Args:
            query: Original query
            resolved_refs: Resolved references
            
        Returns:
            Summary dict
        """
        return {
            'original_query': query,
            'references_detected': len(self.detector.detect(query)),
            'references_resolved': len(resolved_refs),
            'resolution_rate': len(resolved_refs) / len(self.detector.detect(query)) if self.detector.detect(query) else 0,
            'resolved_entities': [ref.resolved_entity for ref in resolved_refs],
            'avg_confidence': sum(r.confidence for r in resolved_refs) / len(resolved_refs) if resolved_refs else 0,
            'sources': [ref.source for ref in resolved_refs]
        }
