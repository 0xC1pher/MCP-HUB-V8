"""
Reference Detector - Detect Contextual References in Queries
Identifies when users refer to previous context
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class ReferenceType(Enum):
    """Types of references"""
    DEMONSTRATIVE = "demonstrative"  # "that function", "this class"
    PRONOUN = "pronoun"  # "it", "them"
    PREVIOUS = "previous"  # "the previous bug", "last function"
    IMPLICIT = "implicit"  # "the function" (when context is clear)


class Reference:
    """Detected reference in text"""
    
    def __init__(
        self,
        text: str,
        ref_type: ReferenceType,
        position: int,
        confidence: float = 1.0
    ):
        self.text = text
        self.ref_type = ref_type
        self.position = position
        self.confidence = confidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'type': self.ref_type.value,
            'position': self.position,
            'confidence': self.confidence
        }


class ReferenceDetector:
    """
    Detect contextual references in user queries
    
    Patterns detected:
    - Demonstratives: "that function", "this class", "those bugs"
    - Pronouns: "it", "them", "its"
    - Previous references: "the previous", "last", "earlier"
    - Implicit: "the function" (when only one function in context)
    """
    
    # Reference patterns (compiled regex)
    DEMONSTRATIVE_PATTERNS = [
        r'\b(that|this|these|those)\s+(\w+)',
        r'\b(esa|ese|esta|este|esas|esos|estas|estos)\s+(\w+)',  # Spanish
    ]
    
    PRONOUN_PATTERNS = [
        r'\b(it|its|them|their)\b',
        r'\b(lo|la|los|las|le|les)\b',  # Spanish
    ]
    
    PREVIOUS_PATTERNS = [
        r'\b(the\s+)?(previous|last|earlier|prior)\s+(\w+)',
        r'\b(el|la|los|las)\s+(anterior|previo|último|última)\s+(\w+)',  # Spanish
    ]
    
    IMPLICIT_PATTERNS = [
        r'\bthe\s+(\w+)\b',
        r'\b(el|la)\s+(\w+)\b',  # Spanish
    ]
    
    # Code entity keywords
    ENTITY_KEYWORDS = {
        'function', 'method', 'class', 'module', 'variable', 'bug', 'error',
        'issue', 'feature', 'file', 'código', 'función', 'clase', 'método',
        'archivo', 'error', 'bug', 'problema'
    }
    
    def __init__(self):
        """Initialize reference detector"""
        # Compile patterns
        self.demonstrative_re = [re.compile(p, re.IGNORECASE) for p in self.DEMONSTRATIVE_PATTERNS]
        self.pronoun_re = [re.compile(p, re.IGNORECASE) for p in self.PRONOUN_PATTERNS]
        self.previous_re = [re.compile(p, re.IGNORECASE) for p in self.PREVIOUS_PATTERNS]
        self.implicit_re = [re.compile(p, re.IGNORECASE) for p in self.IMPLICIT_PATTERNS]
        
        logger.info("ReferenceDetector initialized")
    
    def detect(self, query: str) -> List[Reference]:
        """
        Detect all references in a query
        
        Args:
            query: User query text
            
        Returns:
            List of Reference objects
        """
        references = []
        
        # Detect demonstratives
        references.extend(self._detect_demonstratives(query))
        
        # Detect pronouns
        references.extend(self._detect_pronouns(query))
        
        # Detect previous references
        references.extend(self._detect_previous(query))
        
        # Detect implicit references
        references.extend(self._detect_implicit(query))
        
        logger.debug(f"Detected {len(references)} references in query")
        return references
    
    def _detect_demonstratives(self, query: str) -> List[Reference]:
        """Detect demonstrative references"""
        references = []
        
        for pattern in self.demonstrative_re:
            for match in pattern.finditer(query):
                determiner = match.group(1)
                noun = match.group(2)
                
                # Check if noun is a code entity keyword
                if noun.lower() in self.ENTITY_KEYWORDS:
                    ref = Reference(
                        text=match.group(0),
                        ref_type=ReferenceType.DEMONSTRATIVE,
                        position=match.start(),
                        confidence=0.9
                    )
                    references.append(ref)
        
        return references
    
    def _detect_pronouns(self, query: str) -> List[Reference]:
        """Detect pronoun references"""
        references = []
        
        for pattern in self.pronoun_re:
            for match in pattern.finditer(query):
                ref = Reference(
                    text=match.group(0),
                    ref_type=ReferenceType.PRONOUN,
                    position=match.start(),
                    confidence=0.7  # Lower confidence for pronouns
                )
                references.append(ref)
        
        return references
    
    def _detect_previous(self, query: str) -> List[Reference]:
        """Detect 'previous/last' references"""
        references = []
        
        for pattern in self.previous_re:
            for match in pattern.finditer(query):
                # Extract the noun (last group)
                groups = match.groups()
                noun = groups[-1]
                
                if noun.lower() in self.ENTITY_KEYWORDS:
                    ref = Reference(
                        text=match.group(0),
                        ref_type=ReferenceType.PREVIOUS,
                        position=match.start(),
                        confidence=0.85
                    )
                    references.append(ref)
        
        return references
    
    def _detect_implicit(self, query: str) -> List[Reference]:
        """Detect implicit references (e.g., 'the function')"""
        references = []
        
        for pattern in self.implicit_re:
            for match in pattern.finditer(query):
                # Extract noun
                groups = match.groups()
                noun = groups[-1]
                
                if noun.lower() in self.ENTITY_KEYWORDS:
                    # Lower confidence for implicit references
                    ref = Reference(
                        text=match.group(0),
                        ref_type=ReferenceType.IMPLICIT,
                        position=match.start(),
                        confidence=0.6
                    )
                    references.append(ref)
        
        return references
    
    def has_references(self, query: str) -> bool:
        """
        Check if query contains any references
        
        Args:
            query: User query
            
        Returns:
            True if references detected
        """
        return len(self.detect(query)) > 0
    
    def get_reference_types(self, query: str) -> Set[ReferenceType]:
        """
        Get types of references in query
        
        Args:
            query: User query
            
        Returns:
            Set of ReferenceType enums
        """
        references = self.detect(query)
        return {ref.ref_type for ref in references}
    
    def extract_entity_type(self, reference_text: str) -> Optional[str]:
        """
        Extract the entity type from reference text
        
        Args:
            reference_text: Reference text (e.g., "that function")
            
        Returns:
            Entity type (e.g., "function") or None
        """
        text_lower = reference_text.lower()
        
        for keyword in self.ENTITY_KEYWORDS:
            if keyword in text_lower:
                return keyword
        
        return None
    
    def is_code_reference(self, reference: Reference) -> bool:
        """
        Check if reference is about code entities
        
        Args:
            reference: Reference object
            
        Returns:
            True if reference is code-related
        """
        entity_type = self.extract_entity_type(reference.text)
        return entity_type is not None
    
    def get_summary(self, query: str) -> Dict[str, Any]:
        """
        Get summary of references in query
        
        Args:
            query: User query
            
        Returns:
            Summary dict
        """
        references = self.detect(query)
        
        return {
            'has_references': len(references) > 0,
            'reference_count': len(references),
            'reference_types': [ref.ref_type.value for ref in references],
            'references': [ref.to_dict() for ref in references],
            'avg_confidence': sum(r.confidence for r in references) / len(references) if references else 0
        }
