import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).parent))

from core.advanced_features.factual_audit_jepa import FactualAuditJEPA
from core.pretty_logger import PrettyLogger

logger = PrettyLogger()

def test_jepa():
    auditor = FactualAuditJEPA()
    logger.header("AGI-VORTEX: JEPA WORLD MODEL", "Predictive Layer Anti-Hallucination")
    
    # 1. Test Valid Proposal
    # 1. Test Valid Proposal
    query_1 = "¿Cómo se implementa el multi-tenant?"
    proposal_1 = "El sistema usa aislamiento por ForeignKey (TenantModelMixin) con esquemas compartidos en PostgreSQL. Usamos un solo esquema para todos."
    
    print(f"\n[TEST 1] Query: {query_1}")
    result_1 = auditor.audit_proposal(query_1, proposal_1)
    logger.jepa_flow("TEST-VALID", f"Score: {result_1['score']:.2f} - {result_1['status']}")
    print(f"Audit Result: {result_1['message']}")
    
    # 2. Test Hallucination (Violates schema rule)
    query_2 = "¿Cómo se implementa el multi-tenant?"
    proposal_2 = "Deberíamos usar django-tenants para crear esquemas separados de PostgreSQL para cada institución."
    
    print(f"\n[TEST 2] Query: {query_2}")
    result_2 = auditor.audit_proposal(query_2, proposal_2)
    logger.jepa_flow("TEST-HALLUCINATION", f"Score: {result_2['score']:.2f} - {result_2['status']}")
    print(f"Audit Result: {result_2['message']}")
    if result_2["contradictions"]:
        logger.error(f"Contradictions: {result_2['contradictions']}")

    # 3. Test Out of Scope
    query_3 = "What is the best way to bake a cake?"
    proposal_3 = "Preheat the oven to 350 degrees F and mix flour with sugar and eggs."
    
    print(f"\n[TEST 3] Query: {query_3}")
    print(f"Proposal: {proposal_3[:60]}...")
    result_3 = auditor.audit_proposal(query_3, proposal_3)
    print(f"Result: 🔍 {result_3['status']} - {result_3['message']}")

if __name__ == "__main__":
    test_jepa()
