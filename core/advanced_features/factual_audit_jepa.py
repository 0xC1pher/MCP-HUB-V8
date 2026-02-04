import os
import sys
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from core.storage.vector_engine import VectorEngine
from core.shared.token_manager import TokenBudgetManager

logger = logging.getLogger(__name__)

class FactualAuditJEPA:
    """
    Joint-Embedding Predictive Architecture (JEPA) inspired Factual Auditor.
    
    This layer acts as a 'World Model' for the project. It maps the project's
    requirements, rules, and vision into a semantic space and ensures that
    any proposal (code, plan, or answer) remains within the 'logical bounds' 
    of the project reality.
    """
    def __init__(self, config: Optional[Dict] = None, vector_engine=None):
        self.config = config or {
            "context_directory": "data/project_context",
            "audit_threshold": 0.75,
            "consistency_weight": 0.8
        }
        self.context_dir = self.config.get("context_directory", "data/project_context")
        self.threshold = self.config.get("audit_threshold", 0.75)
        self.vector_engine = vector_engine or VectorEngine(config or {})
        
        # Internal Semantic Map of the project
        self.world_map: Dict[str, np.ndarray] = {}
        self.facts: List[Dict] = []
        self._build_world_model()

    def _build_world_model(self):
        """Constructs the latent representation of the project's 'World Model'."""
        if not os.path.exists(self.context_dir):
            os.makedirs(self.context_dir, exist_ok=True)
            return

        if hasattr(logger, 'jepa_flow'):
            logger.jepa_flow("WORLD-BUILD", f"Building JEPA World Model from {self.context_dir}...")
        else:
            logger.info(f"Building JEPA World Model from {self.context_dir}...")
        
        for root, _, files in os.walk(self.context_dir):
            for file in files:
                if file.endswith(('.md', '.txt')):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # We split by headers to have granular facts
                        import re
                        sections = re.split(r'\n#+\s+', '\n' + content)
                        for section in sections:
                            clean_section = section.strip()
                            if not clean_section: continue
                            vector = self.vector_engine.embed_query(clean_section[:1000])
                            
                            fact_id = f"{file}:{clean_section[:40]}"
                            self.facts.append({
                                "source": file,
                                "content": clean_section,
                                "vector": vector
                            })
                            self.world_map[fact_id] = vector
                    except Exception as e:
                        logger.error(f"Error indexing fact {file}: {e}")
        
        if hasattr(logger, 'jepa_flow'):
            logger.jepa_flow("WORLD-MODEL", f"Synchronized: {len(self.facts)} facts indexed.")
        else:
            logger.info(f"WORLD-MODEL: Synchronized {len(self.facts)} facts indexed.")

    def audit_proposal(self, query: str, proposal: str) -> Dict:
        """
        Audits a proposal against the project's World Model using JEPA principles.
        
        1. Predict the 'Ideal State' vector for the query.
        2. Map the 'Observed Proposal' into the same latent space.
        3. Measure divergence and identify contradictions.
        """
        if not self.facts:
            return {
                "score": 1.0, 
                "status": "unverified", 
                "message": "No project context available for audit."
            }

        # 1. Semantic Embedding of Query and Proposal
        query_vec = self.vector_engine.embed_query(query)
        proposal_vec = self.vector_engine.embed_query(proposal)
        
        # 2. Retrieve anchor facts (The logical bounds)
        anchors = []
        for fact in self.facts:
            sim = self.vector_engine.cosine_similarity(query_vec, fact["vector"])
            anchors.append((sim, fact))
        
        anchors.sort(key=lambda x: x[0], reverse=True)
        top_anchors = [a for a in anchors[:3] if a[0] > 0.5]

        if not top_anchors:
            return {
                "score": 1.0, # Neutral if no context
                "status": "unverified",
                "anchors": [],
                "contradictions": [],
                "message": "No project context available for audit."
            }
            
        # 3. Predict Ideal Latent State (Weighted average of relevant facts)
        vector_dim = top_anchors[0][1]["vector"].shape[0]
        ideal_latent_state = np.zeros(vector_dim, dtype=np.float32)
        total_weight = 0
        
        for sim, fact in top_anchors:
            # Weight facts by how relevant they are to the query
            weight = sim
            ideal_latent_state += fact["vector"].astype(np.float32) * weight
            total_weight += weight
            
        if total_weight > 0:
            ideal_latent_state /= total_weight
            
        # 4. Measure Prediction Error (Divergence between Observed Proposal and Predicted World State)
        observed_vec = proposal_vec.astype(np.float32)
        
        # Alignment (Cosine similarity between observed and ideal)
        alignment = self.vector_engine.cosine_similarity(observed_vec, ideal_latent_state)
        
        # 5. Identify specific contradictions (Divergence detection)
        contradictions = []
        for score, fact in top_anchors:
            fact_alignment = self.vector_engine.cosine_similarity(observed_vec, fact["vector"])
            if fact_alignment < 0.4: # Specific fact contradiction
                contradictions.append(f"Proposal contradicts or ignores rules in '{fact['source']}'")

        # Confidence Calibration (Penalize lack of precision)
        final_score = alignment * (1.0 - (0.2 * len(contradictions)))
        final_score = max(0.0, min(1.0, final_score))
        
        # Status mapping
        status = "trusted"
        if final_score < 0.4:
            status = "hallucination_detected"
        elif final_score < 0.5 or contradictions: # Reduced threshold from 0.7 to 0.5
            status = "suspicious"
            
        return {
            "score": float(final_score),
            "alignment": float(alignment),
            "status": status,
            "anchors": [a[1]["source"] for a in top_anchors],
            "contradictions": contradictions,
            "message": f"Factual consistency: {final_score:.2f}. Status: {status}"
        }

    def update_world_model(self):
        """Re-scans files and updates the semantic map."""
        self.world_map = {}
        self.facts = []
        self._build_world_model()
        return "World Model (JEPA) synchronized."
