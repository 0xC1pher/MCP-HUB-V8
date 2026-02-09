"""
Code Guardian - Sistema de Prevención de Duplicación y Autoaprendizaje

Este módulo implementa un "policía" que:
1. Detecta código duplicado ANTES de crearlo
2. Aprende constantemente de los archivos de contexto
3. Es agnóstico a la lógica de negocio
4. Se integra con JEPA World Model para validación contextual (placeholder implementado)
"""

import os
import re
import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.storage.vector_engine import VectorEngine
from core.shared.token_manager import TokenBudgetManager
from core.advanced_features.decorators import visual_tool_decorator

logger = logging.getLogger(__name__)

@dataclass
class CodeSignature:
    """Firma única de un fragmento de código"""
    hash: str
    name: str
    type: str  # 'function', 'class', 'module', 'template', 'model', 'view'
    file_path: str
    line_start: int
    line_end: int
    signature: str  # Firma semántica simplificada
    dependencies: List[str]
    complexity: float
    last_modified: datetime
    context: Dict[str, Any]
    full_content: str  # Contenido completo del bloque de código

@dataclass
class DuplicationAlert:
    """Alerta de duplicación detectada"""
    severity: str  # 'critical', 'warning', 'info'
    message: str
    existing_code: CodeSignature
    proposed_code: CodeSignature
    similarity_score: float
    recommendations: List[str]
    auto_fix_suggestions: List[str]

class CodeGuardian:
    """
    Guardián inteligente de código con autoaprendizaje
    
    Características principales:
    - Detección preventiva de duplicación basada en contenido completo
    - Aprendizaje continuo de contexto con extracción de bloques
    - Integración con JEPA World Model (placeholder)
    - Validación semántica y sintáctica mejorada
    - Sugerencias de auto-reutilización
    """
    
    def __init__(self, config: Optional[Dict] = None, vector_engine=None):
        self.config = config or {
            "similarity_threshold": 0.85,
            "complexity_threshold": 0.7,
            "learning_enabled": True,
            "auto_suggest_enabled": True,
            "max_context_size": 10000,
            "code_types": ['function', 'class', 'module', 'template', 'model', 'view', 'form', 'serializer'],
            "priority_patterns": [
                r'def\s+(\w+)',
                r'class\s+(\w+)',
                r'models\.\w+',
                r'views\.\w+',
                r'templates/\w+',
                r'forms\.\w+',
                r'serializers\.\w+'
            ]
        }
        
        # Inicializar VectorEngine con configuración por defecto
        if vector_engine:
            self.vector_engine = vector_engine
        else:
            from storage.vector_engine import VectorEngine
            default_config = {
                'embedding': {
                    'dimension': 384,
                    'model': 'sentence-transformers/all-MiniLM-L6-v2',
                    'normalize': True,
                    'dtype': 'float16'
                },
                'hnsw': {
                    'ef_construction': 200,
                    'M': 16,
                    'ef_search': 50
                }
            }
            self.vector_engine = VectorEngine(default_config)
        self.token_manager = TokenBudgetManager()
        
        # Base de conocimiento de código
        self.code_knowledge: Dict[str, CodeSignature] = {}
        self.duplication_history: List[DuplicationAlert] = []
        self.learning_patterns: Dict[str, int] = {}  # Patrones aprendidos
        
        # Índices para búsqueda rápida
        self.name_index: Dict[str, List[str]] = {}
        self.type_index: Dict[str, List[str]] = {}
        self.dependency_index: Dict[str, List[str]] = {}
        
        # Inicializar con contexto existente
        self._build_knowledge_base()
    
    def _build_knowledge_base(self):
        """Construye base de conocimiento desde archivos de contexto"""
        logger.info("🔍 Code Guardian: Construyendo base de conocimiento...")
        
        context_paths = [
            "data/project_context",
            "data/extended_knowledge",
            "data/skills"
        ]
        
        for base_path in context_paths:
            if os.path.exists(base_path):
                self._scan_directory(base_path)
        
        logger.info(f"✅ Code Guardian: Base construida con {len(self.code_knowledge)} elementos")
    
    def _scan_directory(self, directory: str):
        """Escanea directorio en busca de código para aprender"""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.py', '.js', '.html', '.css')):  # Eliminado .md y .json ya que no son código ejecutable primario
                    file_path = os.path.join(root, file)
                    try:
                        self._analyze_file(file_path)
                    except Exception as e:
                        logger.error(f"Error analizando {file_path}: {e}")
    
    def _analyze_file(self, file_path: str):
        """Analiza un archivo y extrae firmas de código"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer diferentes tipos de código
        if file_path.endswith('.py'):
            self._extract_python_signatures(content, file_path)
        elif file_path.endswith('.html'):
            self._extract_template_signatures(content, file_path)
        elif file_path.endswith('.js'):
            self._extract_javascript_signatures(content, file_path)
        elif file_path.endswith('.css'):
            self._extract_css_signatures(content, file_path)
    
    def _find_python_block(self, lines: List[str], start: int) -> Tuple[str, int]:
        """Encuentra el bloque completo de una función o clase en Python basado en indentación"""
        base_indent = len(lines[start]) - len(lines[start].lstrip())
        end = start + 1
        while end < len(lines):
            line = lines[end]
            if line.strip() and (len(line) - len(line.lstrip())) <= base_indent:
                break
            end += 1
        block = '\n'.join(lines[start:end])
        return block, end
    
    def _extract_python_signatures(self, content: str, file_path: str):
        """Extrae firmas de código Python con contenido completo del bloque"""
        lines = content.split('\n')
        
        # Buscar funciones
        for i, line in enumerate(lines):
            func_match = re.search(r'def\s+(\w+)\s*\((.*?)\)', line)
            if func_match:
                block, end_line = self._find_python_block(lines, i)
                self._create_signature(
                    name=func_match.group(1),
                    type='function',
                    file_path=file_path,
                    line_start=i+1,
                    line_end=end_line,
                    content=block,
                    signature=f"def {func_match.group(1)}({func_match.group(2)})"
                )
        
        # Buscar clases
        for i, line in enumerate(lines):
            class_match = re.search(r'class\s+(\w+)(?:\((.*?)\))?', line)
            if class_match:
                block, end_line = self._find_python_block(lines, i)
                self._create_signature(
                    name=class_match.group(1),
                    type='class',
                    file_path=file_path,
                    line_start=i+1,
                    line_end=end_line,
                    content=block,
                    signature=f"class {class_match.group(1)}"
                )
    
    def _extract_template_signatures(self, content: str, file_path: str):
        """Extrae firmas de templates HTML (ej. Django/Jinja)"""
        name = Path(file_path).stem
        # Buscar bloques {% block name %}
        block_matches = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
        if block_matches:
            for block_name in block_matches:
                self._create_signature(
                    name=block_name,
                    type='template_block',
                    file_path=file_path,
                    line_start=1,
                    line_end=len(content.split('\n')),
                    content=content,
                    signature=f"block {block_name}"
                )
        else:
            # Si no hay bloques, usar el template completo
            self._create_signature(
                name=name,
                type='template',
                file_path=file_path,
                line_start=1,
                line_end=len(content.split('\n')),
                content=content,
                signature=f"template {name}"
            )
    
    def _find_js_block(self, lines: List[str], start: int) -> Tuple[str, int]:
        """Encuentra el bloque completo en JS basado en llaves {}"""
        brace_count = 0
        end = start
        in_block = False
        while end < len(lines):
            line = lines[end]
            brace_count += line.count('{') - line.count('}')
            if '{' in line:
                in_block = True
            if in_block and brace_count <= 0:
                end += 1
                break
            end += 1
        block = '\n'.join(lines[start:end])
        return block, end
    
    def _extract_javascript_signatures(self, content: str, file_path: str):
        """Extrae firmas de código JavaScript con bloques"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Funciones tradicionales y arrow
            func_match = re.search(r'(?:function\s+(\w+)\s*\((.*?)\))|(?:const|let|var)\s+(\w+)\s*=\s*(?:\((.*?)\)|(\w+))\s*=>', line)
            if func_match:
                name = func_match.group(1) or func_match.group(3)
                params = func_match.group(2) or func_match.group(4) or func_match.group(5) or ''
                block, end_line = self._find_js_block(lines, i)
                self._create_signature(
                    name=name,
                    type='function',
                    file_path=file_path,
                    line_start=i+1,
                    line_end=end_line,
                    content=block,
                    signature=f"function {name}({params})"
                )
        
        # Clases
        for i, line in enumerate(lines):
            class_match = re.search(r'class\s+(\w+)', line)
            if class_match:
                block, end_line = self._find_js_block(lines, i)
                self._create_signature(
                    name=class_match.group(1),
                    type='class',
                    file_path=file_path,
                    line_start=i+1,
                    line_end=end_line,
                    content=block,
                    signature=f"class {class_match.group(1)}"
                )
    
    def _extract_css_signatures(self, content: str, file_path: str):
        """Extrae selectores CSS como firmas"""
        name = Path(file_path).stem
        selectors = re.findall(r'([^\s{}]+)\s*{', content)
        for selector in set(selectors):
            self._create_signature(
                name=selector.strip(),
                type='css_selector',
                file_path=file_path,
                line_start=1,
                line_end=len(content.split('\n')),
                content=content,
                signature=f"selector {selector}"
            )
    
    def _normalize_code(self, code: str) -> str:
        """Normaliza el código eliminando comentarios, espacios en blanco y líneas vacías"""
        lines = []
        in_multiline_comment = False
        for line in code.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('"""') or line.startswith("'''"):
                in_multiline_comment = not in_multiline_comment
                continue
            if in_multiline_comment:
                continue
            if line.startswith('#') or line.startswith('//') or line.startswith('/*'):
                continue
            lines.append(line)
        return '\n'.join(lines)
    
    def _create_signature(self, name: str, type: str, file_path: str, 
                          line_start: int, content: str, signature: str,
                          line_end: Optional[int] = None) -> CodeSignature:
        """Crea una firma de código única con normalización"""
        
        normalized_content = self._normalize_code(content)
        
        # Calcular hash único basado en contenido normalizado
        code_hash = hashlib.md5(normalized_content.encode()).hexdigest()
        
        # Extraer dependencias
        dependencies = self._extract_dependencies(content)
        
        # Calcular complejidad
        complexity = self._calculate_complexity(content)
        
        # Crear firma
        code_sig = CodeSignature(
            hash=code_hash,
            name=name,
            type=type,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end or line_start + len(content.split('\n')),
            signature=signature,
            dependencies=dependencies,
            complexity=complexity,
            last_modified=datetime.now(),
            context={"source": "context_analysis"},
            full_content=normalized_content
        )
        
        # Almacenar en base de conocimiento si no existe duplicado exacto
        if code_hash not in self.code_knowledge:
            self.code_knowledge[code_hash] = code_sig
            
            # Actualizar índices
            self.name_index.setdefault(name, []).append(code_hash)
            self.type_index.setdefault(type, []).append(code_hash)
            for dep in dependencies:
                self.dependency_index.setdefault(dep, []).append(code_hash)
        
        return code_sig
    
    def check_code_creation(self, proposed_name: str, proposed_type: str, 
                            proposed_content: str, context: Optional[Dict] = None) -> DuplicationAlert:
        """
        Verifica si el código propuesto ya existe antes de crearlo
        
        Returns:
            DuplicationAlert: Alerta detallada con recomendaciones
        """
        logger.info(f"🔍 Code Guardian: Verificando {proposed_type} '{proposed_name}'")
        
        # Crear firma temporal del código propuesto
        temp_signature = self._create_temp_signature(
            proposed_name, proposed_type, proposed_content, context
        )
        
        # Validación con JEPA (placeholder)
        if not self._validate_with_jepa(temp_signature):
            return DuplicationAlert(
                severity='critical',
                message="🚨 CRÍTICO: Fallo en validación contextual con JEPA World Model",
                existing_code=None,
                proposed_code=temp_signature,
                similarity_score=0.0,
                recommendations=["Revisar contexto con JEPA"],
                auto_fix_suggestions=[]
            )
        
        # Buscar duplicados potenciales
        similar_codes = self._find_similar_codes(temp_signature)
        
        if not similar_codes:
            return DuplicationAlert(
                severity='info',
                message=f"✅ No se detectaron duplicados para '{proposed_name}'",
                existing_code=None,
                proposed_code=temp_signature,
                similarity_score=0.0,
                recommendations=["El código puede ser creado de forma segura"],
                auto_fix_suggestions=[]
            )
        
        # Análisis detallado de duplicación
        best_match = max(similar_codes, key=lambda x: x['similarity'])
        existing_code = best_match['code']
        similarity = best_match['similarity']
        
        if similarity >= self.config["similarity_threshold"]:
            severity = 'critical'
            message = f"🚨 CRÍTICO: '{proposed_name}' es {similarity:.1%} similar a '{existing_code.name}'"
            recommendations = [
                f"Reutilizar la función/clase existente: {existing_code.name}",
                f"Verificar en: {existing_code.file_path}:{existing_code.line_start}",
                "Considerar extender la funcionalidad existente en lugar de duplicarla",
                "Si es necesario un comportamiento diferente, usar herencia o composición"
            ]
            auto_fix = [
                f"Importar desde: {existing_code.file_path}",
                f"Extender la clase {existing_code.name}",
                f"Crear wrapper que reutilice {existing_code.name}"
            ]
        elif similarity >= 0.7:
            severity = 'warning'
            message = f"⚠️ ADVERTENCIA: '{proposed_name}' tiene {similarity:.1%} similitud con '{existing_code.name}'"
            recommendations = [
                "Revisar la funcionalidad existente antes de proceder",
                "Considerar si es una variación necesaria o una duplicación",
                "Documentar por qué se necesita una implementación separada"
            ]
            auto_fix = [
                "Refactorizar para compartir lógica común",
                "Crear función auxiliar para código compartido"
            ]
        else:
            severity = 'info'
            message = f"ℹ️ Similitud detectada: '{proposed_name}' vs '{existing_code.name}' ({similarity:.1%})"
            recommendations = ["Considerar si hay oportunidad de reutilización"]
            auto_fix = []
        
        alert = DuplicationAlert(
            severity=severity,
            message=message,
            existing_code=existing_code,
            proposed_code=temp_signature,
            similarity_score=similarity,
            recommendations=recommendations,
            auto_fix_suggestions=auto_fix
        )
        
        # Registrar para aprendizaje
        self.duplication_history.append(alert)
        self._update_learning_patterns(alert)
        
        return alert
    
    def _validate_with_jepa(self, signature: CodeSignature) -> bool:
        """Placeholder para integración con JEPA World Model"""
        # Aquí iría la llamada real a JEPA para validación contextual
        # Por ejemplo: jepa_model.validate(signature.full_content, signature.context)
        logger.info("🔄 Validando con JEPA World Model (placeholder)...")
        return True  # Siempre verdadero hasta implementación real
    
    def _find_similar_codes(self, signature: CodeSignature) -> List[Dict]:
        """Busca códigos similares usando múltiples estrategias"""
        similar_codes = []
        
        # Búsqueda por nombre (rápida)
        if signature.name in self.name_index:
            for code_hash in self.name_index[signature.name]:
                existing = self.code_knowledge[code_hash]
                similarity = self._calculate_similarity(signature, existing)
                if similarity > 0.5:  # Umbral mínimo
                    similar_codes.append({
                        'code': existing,
                        'similarity': similarity,
                        'method': 'name_match'
                    })
        
        # Búsqueda por tipo y dependencias
        if signature.type in self.type_index:
            for code_hash in self.type_index[signature.type]:
                existing = self.code_knowledge[code_hash]
                similarity = self._calculate_similarity(signature, existing)
                if similarity > 0.6:
                    similar_codes.append({
                        'code': existing,
                        'similarity': similarity,
                        'method': 'type_dependency'
                    })
        
        # Búsqueda semántica con vectores (profunda)
        if self.vector_engine:
            semantic_similar = self._semantic_search(signature)
            similar_codes.extend(semantic_similar)
        
        return similar_codes
    
    def _calculate_similarity(self, sig1: CodeSignature, sig2: CodeSignature) -> float:
        """Calcula similitud multidimensional entre dos fragmentos de código, incluyendo contenido completo"""
        
        # Similitud de nombre (20%)
        name_sim = self._string_similarity(sig1.name, sig2.name)
        
        # Similitud de tipo (10%)
        type_sim = 1.0 if sig1.type == sig2.type else 0.0
        
        # Similitud de dependencias (20%)
        dep_sim = self._dependency_similarity(sig1.dependencies, sig2.dependencies)
        
        # Similitud de complejidad (10%)
        complexity_diff = abs(sig1.complexity - sig2.complexity)
        complexity_sim = max(0, 1.0 - complexity_diff)
        
        # Similitud de firma (10%)
        signature_sim = self._string_similarity(sig1.signature, sig2.signature)
        
        # Similitud de contenido completo (30%)
        content_sim = self._string_similarity(sig1.full_content, sig2.full_content)
        
        # Ponderación total
        total_similarity = (
            name_sim * 0.20 +
            type_sim * 0.10 +
            dep_sim * 0.20 +
            complexity_sim * 0.10 +
            signature_sim * 0.10 +
            content_sim * 0.30
        )
        
        return total_similarity
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calcula similitud de cadenas usando distancia de Levenshtein"""
        if not s1 or not s2:
            return 0.0
        
        # Normalizar
        s1, s2 = s1.lower(), s2.lower()
        
        # Calcular distancia
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return 1.0
        
        # Distancia de Levenshtein simplificada
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len)
    
    def _dependency_similarity(self, deps1: List[str], deps2: List[str]) -> float:
        """Calcula similitud de dependencias"""
        if not deps1 and not deps2:
            return 1.0
        if not deps1 or not deps2:
            return 0.0
        
        set1, set2 = set(deps1), set(deps2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _semantic_search(self, signature: CodeSignature) -> List[Dict]:
        """Búsqueda semántica usando embeddings del contenido completo"""
        try:
            # Crear embedding del contenido normalizado
            signature_vector = self.vector_engine.embed_query(signature.full_content)
            
            similar_codes = []
            for code_hash, existing_code in self.code_knowledge.items():
                existing_vector = self.vector_engine.embed_query(existing_code.full_content)
                
                # Calcular similitud coseno
                similarity = self.vector_engine.cosine_similarity(
                    signature_vector, existing_vector
                )
                
                if similarity > 0.7:  # Umbral semántico
                    similar_codes.append({
                        'code': existing_code,
                        'similarity': similarity,
                        'method': 'semantic'
                    })
            
            return similar_codes
        except Exception as e:
            logger.error(f"Error en búsqueda semántica: {e}")
            return []
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extrae dependencias del código"""
        dependencies = []
        
        # Importaciones Python/JS
        imports = re.findall(r'^(?:from|import|require)\s+[\'"](.+?)[\'"]', content, re.MULTILINE)
        dependencies.extend(imports)
        
        # Modelos Django
        models = re.findall(r'(\w+)\.objects', content)
        dependencies.extend(models)
        
        # Templates
        templates = re.findall(r'{%\s*extends\s+[\'"](\w+)[\'"]\s*%}', content)
        dependencies.extend(templates)
        
        return list(set(dependencies))
    
    def _calculate_complexity(self, content: str) -> float:
        """Calcula complejidad ciclomática aproximada"""
        complexity_indicators = [
            r'\bif\b', r'\belif\b', r'\belse\b',  # Condicionales
            r'\bfor\b', r'\bwhile\b',           # Bucles
            r'\btry\b', r'\bexcept\b',          # Manejo de errores
            r'\band\b', r'\bor\b',              # Operadores lógicos
            r'\bdef\b', r'\bclass\b',           # Definiciones
            r'\bfunction\b', r'\bclass\b'       # JS
        ]
        
        total_complexity = 0
        for pattern in complexity_indicators:
            matches = re.findall(pattern, content, re.IGNORECASE)
            total_complexity += len(matches)
        
        # Normalizar entre 0 y 1
        return min(1.0, total_complexity / 50.0)
    
    def _create_temp_signature(self, name: str, type: str, content: str, 
                               context: Optional[Dict] = None) -> CodeSignature:
        """Crea una firma temporal para código propuesto"""
        signature = f"{type} {name}"
        normalized_content = self._normalize_code(content)
        code_hash = hashlib.md5(normalized_content.encode()).hexdigest()
        
        return CodeSignature(
            hash=code_hash,
            name=name,
            type=type,
            file_path="proposed",
            line_start=0,
            line_end=len(content.split('\n')),
            signature=signature,
            dependencies=self._extract_dependencies(content),
            complexity=self._calculate_complexity(content),
            last_modified=datetime.now(),
            context=context or {},
            full_content=normalized_content
        )
    
    def _update_learning_patterns(self, alert: DuplicationAlert):
        """Actualiza patrones de aprendizaje basados en alertas"""
        if not self.config["learning_enabled"]:
            return
        
        # Aprender de patrones de duplicación
        pattern_key = f"{alert.proposed_code.type}:{alert.proposed_code.name}"
        self.learning_patterns[pattern_key] = self.learning_patterns.get(pattern_key, 0) + 1
        
        # Si hay muchas duplicaciones del mismo patrón, aumentar sensibilidad
        if self.learning_patterns[pattern_key] > 3:
            logger.warning(f"🔄 Patrón de duplicación detectado: {pattern_key}")
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del aprendizaje del guardián"""
        return {
            "total_code_elements": len(self.code_knowledge),
            "duplication_alerts": len(self.duplication_history),
            "learning_patterns": len(self.learning_patterns),
            "most_problematic_patterns": sorted(
                self.learning_patterns.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            "recommendations": self._generate_learning_recommendations()
        }
    
    def _generate_learning_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en aprendizaje"""
        recommendations = []
        
        # Analizar patrones frecuentes
        for pattern, count in self.learning_patterns.items():
            if count > 2:
                pattern_type, pattern_name = pattern.split(':', 1)
                recommendations.append(
                    f"Se ha detectado duplicación frecuente de {pattern_type}s '{pattern_name}' "
                    f"({count} veces). Considerar crear una implementación reutilizable."
                )
        
        # Analizar tipos problemáticos
        if self.type_index:
            for code_type, hashes in self.type_index.items():
                if len(hashes) > 20:  # Muchos elementos del mismo tipo
                    recommendations.append(
                        f"Hay {len(hashes)} elementos de tipo '{code_type}'. "
                        f"Considerar refactorización o abstracción."
                    )
        
        return recommendations
    
    def suggest_reuse_alternatives(self, proposed_name: str, proposed_type: str) -> List[Dict[str, Any]]:
        """Sugiere alternativas de reutilización para código propuesto"""
        alternatives = []
        
        # Buscar funciones/clases similares que podrían ser extendidas
        if proposed_name in self.name_index:
            for code_hash in self.name_index[proposed_name]:
                existing = self.code_knowledge[code_hash]
                if existing.type == proposed_type:
                    alternatives.append({
                        "action": "extend",
                        "target": existing.name,
                        "file_path": existing.file_path,
                        "explanation": f"Extender la {proposed_type} existente '{existing.name}'"
                    })
        
        # Buscar funciones auxiliares que podrían ser útiles
        for code_hash, code in self.code_knowledge.items():
            if code.type == 'function' and code.name != proposed_name:
                # Verificar si podría ser útil como helper
                if self._could_be_helper(proposed_name, code.name):
                    alternatives.append({
                        "action": "use_helper",
                        "target": code.name,
                        "file_path": code.file_path,
                        "explanation": f"Usar la función auxiliar '{code.name}'"
                    })
        
        return alternatives
    
    def _could_be_helper(self, proposed_name: str, existing_name: str) -> bool:
        """Determina si una función existente podría ser helper para la propuesta"""
        # Análisis simple basado en nombres y patrones
        proposed_words = set(proposed_name.lower().split('_'))
        existing_words = set(existing_name.lower().split('_'))
        
        # Si comparten muchas palabras, podría ser útil
        shared_words = proposed_words.intersection(existing_words)
        return len(shared_words) > 1  # Aumentado umbral para más precisión


# Decorador para integración con herramientas existentes
def code_guardian_check(code_type: str, auto_suggest: bool = True):
    """
    Decorador que verifica duplicación antes de crear código
    
    Usage:
        @code_guardian_check('function')
        def create_new_function(name: str, content: str):
            # El guardián verificará antes de permitir la creación
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Obtener instancia del guardián
            guardian = CodeGuardian()
            
            # Extraer información del código propuesto
            proposed_name = kwargs.get('name', args[0] if args else 'unknown')
            proposed_content = kwargs.get('content', args[1] if len(args) > 1 else '')
            
            # Verificar duplicación
            alert = guardian.check_code_creation(
                proposed_name=proposed_name,
                proposed_type=code_type,
                proposed_content=proposed_content,
                context={'function': func.__name__, 'args': args, 'kwargs': kwargs}
            )
            
            # Si es crítico, detener la creación
            if alert.severity == 'critical':
                logger.error(f"🚨 Code Guardian DETENIÓ la creación: {alert.message}")
                logger.info(f"💡 Alternativas: {alert.auto_fix_suggestions}")
                
                # Si hay auto-sugerencias activadas
                if auto_suggest and alert.auto_fix_suggestions:
                    return {
                        'status': 'prevented',
                        'alert': alert,
                        'suggestions': alert.auto_fix_suggestions,
                        'alternatives': guardian.suggest_reuse_alternatives(proposed_name, code_type)
                    }
                else:
                    raise ValueError(f"Code Guardian: {alert.message}")
            
            # Si es advertencia, loguear pero permitir
            if alert.severity == 'warning':
                logger.warning(f"⚠️ Code Guardian ADVERTENCIA: {alert.message}")
                logger.info(f"💡 Recomendaciones: {alert.recommendations}")
            
            # Proceder con la función original
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class CodeGuardianMCP(CodeGuardian):
    """
    Extensión MCP del Code Guardian con herramientas de integración
    """
    
    def __init__(self, config: Optional[Dict] = None, vector_engine=None):
        super().__init__(config, vector_engine)
        logger.info("🛡️ Code Guardian MCP inicializado con herramientas de integración")
    
    @visual_tool_decorator("🛡️ PREVIENE duplicación ANTES de crear código")
    def check_code_creation(self, code_content: str, file_path: str, code_type: str = "function") -> Dict[str, Any]:
        """
        Verifica si el código que se quiere crear ya existe
        
        Args:
            code_content: Contenido del código propuesto
            file_path: Ruta del archivo donde se crearía
            code_type: Tipo de código (function, class, module, etc.)
            
        Returns:
            Dict con resultado de la verificación y sugerencias
        """
        logger.info(f"🔍 Verificando código duplicado para {code_type} en {file_path}")
        
        # Crear firma temporal del código propuesto
        proposed_signature = self._create_signature(
            name=f"proposed_{code_type}",
            type=code_type,
            file_path=file_path,
            line_start=0,
            content=code_content,
            signature=f"{code_type} proposed_{code_type}"
        )
        
        # Buscar duplicados
        alert = self._check_duplication(proposed_signature)
        
        if alert:
            return {
                "can_create": False,
                "alert": alert,
                "suggestions": self._suggest_reuse(alert),
                "message": f"⚠️ Código duplicado detectado: {alert.message}"
            }
        
        return {
            "can_create": True,
            "alert": None,
            "suggestions": [],
            "message": "✅ No se detectaron duplicaciones"
        }
    
    @visual_tool_decorator("📊 ANALIZA redundancia en TODO el proyecto")
    def analyze_project_redundancy(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analiza el proyecto completo en busca de redundancias
        
        Args:
            project_path: Ruta del proyecto (opcional, usa el actual por defecto)
            
        Returns:
            Dict con análisis de redundancia y estadísticas
        """
        if not project_path:
            project_path = os.getcwd()
            
        logger.info(f"📊 Analizando redundancia en proyecto: {project_path}")
        
        # Reconstruir base de conocimiento
        self._build_knowledge_base()
        
        # Buscar patrones de duplicación
        redundancy_report = self._find_redundancy_patterns()
        
        return {
            "project_path": project_path,
            "total_signatures": len(self.code_knowledge),
            "redundancy_patterns": redundancy_report,
            "learning_patterns": self.learning_patterns,
            "recommendations": self._generate_redundancy_recommendations(redundancy_report)
        }
    
    @visual_tool_decorator("💡 SUGIERE código reutilizable existente")
    def get_code_suggestions(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Sugiere código existente que podría ser reutilizado
        
        Args:
            query: Descripción del código que se necesita
            limit: Número máximo de sugerencias
            
        Returns:
            Dict con sugerencias de código reutilizable
        """
        logger.info(f"💡 Buscando sugerencias para: {query}")
        
        # Buscar en el vector engine
        suggestions = self._search_similar_code(query, limit)
        
        return {
            "query": query,
            "suggestions": suggestions,
            "total_found": len(suggestions),
            "message": f"Encontradas {len(suggestions)} sugerencias de reutilización"
        }
    
    @visual_tool_decorator("🧠 APRENDE de archivos de contexto")
    def learn_from_context(self, context_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Aprende de archivos de contexto específicos
        
        Args:
            context_files: Lista de archivos para aprender (opcional)
            
        Returns:
            Dict con resultados del aprendizaje
        """
        if not context_files:
            context_files = [
                "data/project_context/context.md",
                "data/extended_knowledge",
                "data/skills"
            ]
        
        logger.info(f"🧠 Aprendiendo de contexto: {context_files}")
        
        # Procesar archivos de contexto
        learned_items = 0
        for context_file in context_files:
            if os.path.exists(context_file):
                if os.path.isfile(context_file):
                    self._learn_from_file(context_file)
                    learned_items += 1
                elif os.path.isdir(context_file):
                    self._scan_directory(context_file)
                    learned_items += 1
        
        return {
            "context_files": context_files,
            "learned_items": learned_items,
            "total_knowledge": len(self.code_knowledge),
            "message": f"Aprendidos {learned_items} elementos de contexto"
        }
    
    def _check_duplication(self, proposed_signature: CodeSignature) -> Optional[DuplicationAlert]:
        """Verifica si hay duplicación con firma existente"""
        # Buscar por hash exacto
        if proposed_signature.hash in self.code_knowledge:
            existing = self.code_knowledge[proposed_signature.hash]
            return DuplicationAlert(
                severity='critical',
                message=f"Código idéntico encontrado en {existing.file_path}",
                existing_code=existing,
                proposed_code=proposed_signature,
                similarity_score=1.0,
                recommendations=[f"Reutilizar código de {existing.file_path}"],
                auto_fix_suggestions=[f"Importar desde {existing.file_path}"]
            )
        
        # Buscar por similitud semántica
        for existing_hash, existing_signature in self.code_knowledge.items():
            similarity = self._calculate_similarity(proposed_signature, existing_signature)
            
            if similarity >= self.config["similarity_threshold"]:
                return DuplicationAlert(
                    severity='warning' if similarity < 0.95 else 'critical',
                    message=f"Código muy similar encontrado en {existing_signature.file_path}",
                    existing_code=existing_signature,
                    proposed_code=proposed_signature,
                    similarity_score=similarity,
                    recommendations=[
                        f"Considerar reutilizar {existing_signature.name} de {existing_signature.file_path}",
                        "Refactorizar para evitar duplicación"
                    ],
                    auto_fix_suggestions=[
                        f"Crear función compartida en módulo común",
                        f"Usar herencia o composición"
                    ]
                )
        
        return None
    
    def _suggest_reuse(self, alert: DuplicationAlert) -> List[Dict[str, Any]]:
        """Sugiere cómo reutilizar el código existente"""
        suggestions = []
        
        existing = alert.existing_code
        
        suggestions.append({
            "type": "import",
            "description": f"Importar desde {existing.file_path}",
            "code": f"from {existing.file_path.replace('/', '.').replace('.py', '')} import {existing.name}",
            "applicability": "high"
        })
        
        if existing.type == "function":
            suggestions.append({
                "type": "function_call",
                "description": f"Llamar a la función existente {existing.name}",
                "code": f"{existing.name}()",
                "applicability": "high"
            })
        
        elif existing.type == "class":
            suggestions.append({
                "type": "inheritance",
                "description": f"Heredar de la clase existente {existing.name}",
                "code": f"class NuevaClase({existing.name}):\n    pass",
                "applicability": "medium"
            })
            
            suggestions.append({
                "type": "composition",
                "description": f"Componer con la clase existente {existing.name}",
                "code": f"class NuevaClase:\n    def __init__(self):\n        self.{existing.name.lower()} = {existing.name}()",
                "applicability": "medium"
            })
        
        return suggestions
    
    def _find_redundancy_patterns(self) -> List[Dict[str, Any]]:
        """Encuentra patrones de redundancia en el código"""
        patterns = []
        
        # Agrupar por tipo
        by_type = {}
        for code_hash, signature in self.code_knowledge.items():
            if signature.type not in by_type:
                by_type[signature.type] = []
            by_type[signature.type].append(signature)
        
        # Buscar redundancias por tipo
        for code_type, signatures in by_type.items():
            if len(signatures) > 1:
                # Buscar similitudes dentro del mismo tipo
                for i, sig1 in enumerate(signatures):
                    for j, sig2 in enumerate(signatures[i+1:], i+1):
                        similarity = self._calculate_similarity(sig1, sig2)
                        if similarity >= self.config["similarity_threshold"]:
                            patterns.append({
                                "type": code_type,
                                "similarity": similarity,
                                "files": [sig1.file_path, sig2.file_path],
                                "names": [sig1.name, sig2.name],
                                "recommendation": f"Considerar refactorización de {code_type}s similares"
                            })
        
        return patterns
    
    def _generate_redundancy_recommendations(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Genera recomendaciones para reducir redundancia"""
        recommendations = []
        
        if patterns:
            recommendations.append(f"Se encontraron {len(patterns)} patrones de redundancia")
            
            # Agrupar por tipo
            by_type = {}
            for pattern in patterns:
                code_type = pattern["type"]
                if code_type not in by_type:
                    by_type[code_type] = 0
                by_type[code_type] += 1
            
            for code_type, count in by_type.items():
                recommendations.append(f"- {count} redundancias en {code_type}s")
                recommendations.append(f"  Sugerencia: Crear un módulo compartido para {code_type}s")
        
        else:
            recommendations.append("No se detectaron patrones de redundancia significativos")
        
        return recommendations
    
    def _search_similar_code(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Busca código similar usando el vector engine"""
        # Usar el vector engine para buscar similitud semántica
        similar_codes = []
        
        # Buscar en las firmas existentes
        for code_hash, signature in self.code_knowledge.items():
            # Calcular relevancia basada en el query
            relevance = self._calculate_query_relevance(query, signature)
            
            if relevance > 0.5:  # Umbral de relevancia
                similar_codes.append({
                    "signature": signature,
                    "relevance": relevance,
                    "suggestion": f"Reutilizar {signature.name} de {signature.file_path}",
                    "code_preview": signature.full_content[:200] + "..." if len(signature.full_content) > 200 else signature.full_content
                })
        
        # Ordenar por relevancia y limitar
        similar_codes.sort(key=lambda x: x["relevance"], reverse=True)
        return similar_codes[:limit]
    
    def _calculate_query_relevance(self, query: str, signature: CodeSignature) -> float:
        """Calcula la relevancia de una firma respecto a un query"""
        query_lower = query.lower()
        name_lower = signature.name.lower()
        
        # Coincidencia exacta en nombre
        if query_lower in name_lower or name_lower in query_lower:
            return 1.0
        
        # Coincidencia parcial
        query_words = query_lower.split()
        name_words = name_lower.split("_")
        
        matches = 0
        for q_word in query_words:
            for n_word in name_words:
                if q_word in n_word or n_word in q_word:
                    matches += 1
                    break
        
        return matches / max(len(query_words), len(name_words))
    
    def _learn_from_file(self, file_path: str):
        """Aprende de un archivo específico"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Analizar según el tipo de archivo
            if file_path.endswith('.py'):
                self._extract_python_signatures(content, file_path)
            elif file_path.endswith('.html'):
                self._extract_template_signatures(content, file_path)
            elif file_path.endswith('.js'):
                self._extract_javascript_signatures(content, file_path)
            elif file_path.endswith('.css'):
                self._extract_css_signatures(content, file_path)
            
            logger.info(f"✅ Aprendido de archivo: {file_path}")
            
        except Exception as e:
            logger.error(f"Error aprendiendo de {file_path}: {e}")
    
    def _extract_css_signatures(self, content: str, file_path: str):
        """Extrae firmas de código CSS"""
        # Patrones para CSS
        css_patterns = [
            (r'\.([\w-]+)\s*\{[^}]+\}', 'class'),
            (r'#([\w-]+)\s*\{[^}]+\}', 'id'),
            (r'([\w-]+)\s*\{[^}]+\}', 'element')
        ]
        
        for pattern, css_type in css_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for i, match in enumerate(matches):
                selector = match.group(1)
                self._create_signature(
                     name=f"{css_type}_{selector}",
                     type='css',
                     file_path=file_path,
                     line_start=content[:match.start()].count('\n') + 1,
                     content=match.group(0),
                     signature=f"{css_type} {selector}"
                 )
    
    def _calculate_similarity(self, sig1: CodeSignature, sig2: CodeSignature) -> float:
        """Calcula similitud multidimensional entre dos fragmentos de código"""
        
        # Similitud de nombre (20%)
        name_sim = self._string_similarity(sig1.name, sig2.name)
        
        # Similitud de tipo (10%)
        type_sim = 1.0 if sig1.type == sig2.type else 0.0
        
        # Similitud de dependencias (25%)
        dep_sim = self._dependency_similarity(sig1.dependencies, sig2.dependencies)
        
        # Similitud de complejidad (15%)
        complexity_diff = abs(sig1.complexity - sig2.complexity)
        complexity_sim = max(0, 1.0 - complexity_diff)
        
        # Similitud de firma (10%)
        signature_sim = self._string_similarity(sig1.signature, sig2.signature)
        
        # Similitud de contenido completo (30%) - NUEVO
        content_sim = self._string_similarity(sig1.full_content, sig2.full_content)
        
        # Ponderación total
        total_similarity = (
            name_sim * 0.20 +
            type_sim * 0.10 +
            dep_sim * 0.25 +
            complexity_sim * 0.15 +
            signature_sim * 0.10 +
            content_sim * 0.30
        )
        
        return total_similarity
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calcula similitud de cadenas usando distancia de Levenshtein"""
        if not s1 or not s2:
            return 0.0
        
        # Implementación simplificada de distancia de Levenshtein
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Calcular similitud basada en caracteres comunes
        common_chars = 0
        min_len = min(len1, len2)
        max_len = max(len1, len2)
        
        for i in range(min_len):
            if s1[i] == s2[i]:
                common_chars += 1
        
        return common_chars / max_len
    
    def _dependency_similarity(self, deps1: List[str], deps2: List[str]) -> float:
        """Calcula similitud entre listas de dependencias"""
        if not deps1 and not deps2:
            return 1.0
        
        if not deps1 or not deps2:
            return 0.0
        
        # Calcular intersección
        set1, set2 = set(deps1), set(deps2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extrae dependencias del código"""
        dependencies = []
        
        # Buscar imports en Python
        import_matches = re.findall(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE)
        dependencies.extend(import_matches)
        
        # Buscar requires en JavaScript
        require_matches = re.findall(r'require\(["\'](\w+)["\']\)', content)
        dependencies.extend(require_matches)
        
        # Buscar imports en JavaScript
        js_import_matches = re.findall(r'import\s+.*?\s+from\s+["\'](\w+)["\']', content)
        dependencies.extend(js_import_matches)
        
        return list(set(dependencies))  # Eliminar duplicados
    
    def _calculate_complexity(self, content: str) -> float:
        """Calcula complejidad del código"""
        lines = content.split('\n')
        
        complexity_factors = {
            'conditionals': len(re.findall(r'\b(if|elif|else|switch|case)\b', content)),
            'loops': len(re.findall(r'\b(for|while|do)\b', content)),
            'functions': len(re.findall(r'\b(def|function)\b', content)),
            'classes': len(re.findall(r'\b(class)\b', content)),
            'nesting': content.count('{') + content.count('}'),
            'total_lines': len(lines)
        }
        
        # Fórmula de complejidad simplificada
        complexity = (
            complexity_factors['conditionals'] * 1.0 +
            complexity_factors['loops'] * 1.5 +
            complexity_factors['functions'] * 0.5 +
            complexity_factors['classes'] * 2.0 +
            complexity_factors['nesting'] * 0.1
        )
        
        # Normalizar por líneas totales
        if complexity_factors['total_lines'] > 0:
            complexity = complexity / complexity_factors['total_lines']
        
        return min(complexity, 1.0)  # Limitar a 1.0
    
    def _extract_python_signatures(self, content: str, file_path: str):
        """Extrae firmas de código Python"""
        # Buscar funciones
        function_pattern = r'def\s+(\w+)\s*\([^)]*\):'
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1)
            start_line = content[:match.start()].count('\n') + 1
            func_content = self._extract_block(content, match.start())
            
            self._create_signature(
                name=func_name,
                type='function',
                file_path=file_path,
                line_start=start_line,
                content=func_content,
                signature=f"def {func_name}"
            )
        
        # Buscar clases
        class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            start_line = content[:match.start()].count('\n') + 1
            class_content = self._extract_block(content, match.start())
            
            self._create_signature(
                name=class_name,
                type='class',
                file_path=file_path,
                line_start=start_line,
                content=class_content,
                signature=f"class {class_name}"
            )
    
    def _extract_javascript_signatures(self, content: str, file_path: str):
        """Extrae firmas de código JavaScript"""
        # Buscar funciones
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{'
        arrow_pattern = r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{'
        
        patterns = [
            (function_pattern, 'function'),
            (arrow_pattern, 'arrow_function')
        ]
        
        for pattern, func_type in patterns:
            for match in re.finditer(pattern, content):
                func_name = match.group(1)
                start_line = content[:match.start()].count('\n') + 1
                func_content = self._extract_js_block(content, match.start())
                
                self._create_signature(
                    name=func_name,
                    type=func_type,
                    file_path=file_path,
                    line_start=start_line,
                    content=func_content,
                    signature=f"function {func_name}"
                )
    
    def _extract_template_signatures(self, content: str, file_path: str):
        """Extrae firmas de templates HTML"""
        # Buscar bloques de template
        template_pattern = r'\{%\s*block\s+(\w+)\s*%\}'
        
        for match in re.finditer(template_pattern, content):
            block_name = match.group(1)
            start_line = content[:match.start()].count('\n') + 1
            block_content = self._extract_template_block(content, match.start())
            
            self._create_signature(
                name=block_name,
                type='template_block',
                file_path=file_path,
                line_start=start_line,
                content=block_content,
                signature=f"block {block_name}"
            )
    
    def _extract_block(self, content: str, start_pos: int) -> str:
        """Extrae un bloque de código Python"""
        lines = content[start_pos:].split('\n')
        block_lines = []
        indent_level = None
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                block_lines.append(line)
                continue
            
            current_indent = len(line) - len(line.lstrip())
            
            if indent_level is None and stripped:
                indent_level = current_indent
            
            if indent_level is not None and current_indent < indent_level and stripped:
                break
            
            block_lines.append(line)
        
        return '\n'.join(block_lines)
    
    def _extract_js_block(self, content: str, start_pos: int) -> str:
        """Extrae un bloque de código JavaScript"""
        # Implementación simplificada - buscar hasta el cierre de llaves
        bracket_count = 0
        block_start = False
        block_content = ""
        
        for i, char in enumerate(content[start_pos:]):
            block_content += char
            
            if char == '{':
                bracket_count += 1
                block_start = True
            elif char == '}':
                bracket_count -= 1
                
            if block_start and bracket_count == 0:
                break
        
        return block_content
    
    def _extract_template_block(self, content: str, start_pos: int) -> str:
        """Extrae un bloque de template Django/Jinja"""
        # Buscar desde {% block nombre %} hasta {% endblock %}
        block_content = ""
        lines = content[start_pos:].split('\n')
        
        for line in lines:
            block_content += line + '\n'
            if '{% endblock %}' in line:
                break
        
        return block_content


def create_code_guardian_mcp_tools():
    """
    Crea y retorna las herramientas MCP del Code Guardian
    
    Returns:
        Dict: Diccionario de herramientas MCP disponibles
    """
    guardian = CodeGuardianMCP()
    
    # Crear las herramientas disponibles como diccionario
    code_guardian_tools = {
        'check_code_creation': guardian.check_code_creation,
        'analyze_project_redundancy': guardian.analyze_project_redundancy,
        'get_code_suggestions': guardian.get_code_suggestions,
        'learn_from_context': guardian.learn_from_context
    }
    
    logger.info(f"🛡️ Code Guardian MCP Tools creadas: {len(code_guardian_tools)} herramientas")
    return code_guardian_tools