"""
Extended Knowledge System - Deep Code Intelligence for MCP v8
==============================================================

Este módulo extiende el conocimiento del MCP más allá de funciones y clases.
Detecta y indexa:

1. ESTRUCTURA DE CÓDIGO:
   - Constantes y variables globales importantes
   - Configuraciones (JSON, YAML, .env)
   - Decoradores personalizados
   - Endpoints/APIs (Django, Flask, FastAPI)
   - Modelos de datos (Django models, dataclasses, Pydantic)
   
2. PATRONES Y ARQUITECTURA:
   - Patrones de diseño detectados
   - Dependencias entre módulos
   - Estructura del proyecto
   
3. DOCUMENTACIÓN:
   - TODOs y FIXMEs
   - Comentarios importantes
   - README y documentación

4. QUALITY GUARDIAN:
   - Principios de código siempre presentes
   - Detección de código duplicado
   - Alertas de escalabilidad
"""

import ast
import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================
# Data Classes para Extended Knowledge
# ============================================

@dataclass
class ConstantInfo:
    """Información sobre constantes y variables globales"""
    name: str
    module: str
    value_type: str
    value_preview: str  # Primeros 100 chars del valor
    line: int
    is_configuration: bool = False


@dataclass
class APIEndpointInfo:
    """Información sobre endpoints/APIs"""
    path: str
    method: str  # GET, POST, PUT, DELETE, etc.
    function_name: str
    module: str
    line: int
    framework: str  # django, flask, fastapi
    docstring: Optional[str] = None


@dataclass
class ModelInfo:
    """Información sobre modelos de datos"""
    name: str
    module: str
    model_type: str  # django, pydantic, dataclass, sqlalchemy
    fields: List[Dict[str, str]]
    line: int
    docstring: Optional[str] = None


@dataclass
class PatternInfo:
    """Patrón de diseño detectado"""
    pattern_name: str
    module: str
    class_name: Optional[str]
    confidence: float  # 0.0 - 1.0
    evidence: str


@dataclass
class TodoItem:
    """TODO/FIXME encontrado en el código"""
    type: str  # TODO, FIXME, HACK, NOTE
    text: str
    module: str
    line: int
    priority: str  # low, medium, high


@dataclass 
class DependencyInfo:
    """Dependencia entre módulos"""
    source_module: str
    target_module: str
    import_type: str  # direct, from
    items_imported: List[str]


# ============================================
# Quality Guardian - Principios de Calidad
# ============================================

class QualityPrinciple(Enum):
    """Principios de calidad de código"""
    NO_REDUNDANCY = "no_redundancy"
    NO_DUPLICATION = "no_duplication"
    SCALABILITY = "scalability"
    SINGLE_RESPONSIBILITY = "single_responsibility"
    DRY = "dry"  # Don't Repeat Yourself
    KISS = "kiss"  # Keep It Simple, Stupid
    SOLID = "solid"


@dataclass
class QualityGuardian:
    """
    Sistema que mantiene principios de calidad siempre presentes.
    
    Esta clase es inyectada en cada respuesta del MCP para recordar
    los principios de código limpio.
    """
    
    # Principios activos
    ACTIVE_PRINCIPLES: List[Dict[str, str]] = field(default_factory=lambda: [
        {
            "id": "no_redundancy",
            "name": "🚫 No Redundancia",
            "description": "No crear código redundante. Reutilizar funciones y componentes existentes.",
            "check": "¿Existe ya algo similar que pueda reutilizar?"
        },
        {
            "id": "no_duplication", 
            "name": "🔄 No Duplicación",
            "description": "No duplicar código. Extraer lógica común a funciones/clases compartidas.",
            "check": "¿Estoy copiando código que ya existe en otro lugar?"
        },
        {
            "id": "scalability",
            "name": "📈 Escalabilidad",
            "description": "Mantener el código escalable. Diseñar para crecimiento futuro.",
            "check": "¿Funcionará con 10x más datos/usuarios?"
        },
        {
            "id": "single_responsibility",
            "name": "🎯 Responsabilidad Única",
            "description": "Cada clase/función debe tener una sola responsabilidad.",
            "check": "¿Esta función hace más de una cosa?"
        },
        {
            "id": "dry",
            "name": "🏜️ DRY (Don't Repeat Yourself)",
            "description": "Cada pieza de conocimiento debe tener una representación única.",
            "check": "¿Hay lógica repetida que deba extraer?"
        }
    ])
    
    def get_reminder(self) -> str:
        """Obtener recordatorio de principios para inyectar en respuestas"""
        reminder = "\n\n⚠️ **QUALITY GUARDIAN - Recordatorio de Principios:**\n"
        for p in self.ACTIVE_PRINCIPLES:
            reminder += f"- {p['name']}: {p['check']}\n"
        return reminder
    
    def get_principles_summary(self) -> str:
        """Obtener resumen completo de principios"""
        summary = "# 🛡️ Quality Guardian - Principios de Código\n\n"
        for p in self.ACTIVE_PRINCIPLES:
            summary += f"## {p['name']}\n"
            summary += f"**Descripción:** {p['description']}\n"
            summary += f"**Pregunta clave:** {p['check']}\n\n"
        return summary
    
    def check_code_quality(self, code: str) -> List[Dict[str, Any]]:
        """
        Analizar código y detectar posibles violaciones de principios.
        
        Args:
            code: Código fuente a analizar
            
        Returns:
            Lista de advertencias y sugerencias
        """
        warnings = []
        
        # Detectar código duplicado (patrones repetidos)
        lines = code.split('\n')
        seen_patterns = {}
        
        for i, line in enumerate(lines):
            clean_line = line.strip()
            if len(clean_line) > 20:  # Solo líneas significativas
                pattern_hash = hashlib.md5(clean_line.encode()).hexdigest()[:8]
                if pattern_hash in seen_patterns:
                    warnings.append({
                        "principle": "no_duplication",
                        "severity": "warning",
                        "line": i + 1,
                        "message": f"Posible duplicación detectada (similar a línea {seen_patterns[pattern_hash] + 1})"
                    })
                else:
                    seen_patterns[pattern_hash] = i
        
        # Detectar funciones muy largas (posible violación de single responsibility)
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_length = (node.end_lineno or node.lineno) - node.lineno
                    if func_length > 50:
                        warnings.append({
                            "principle": "single_responsibility",
                            "severity": "warning",
                            "line": node.lineno,
                            "message": f"Función '{node.name}' tiene {func_length} líneas. Considera dividirla."
                        })
        except Exception:
            pass
        
        # Detectar imports duplicados
        import_pattern = re.compile(r'^(?:from|import)\s+(\S+)', re.MULTILINE)
        imports = import_pattern.findall(code)
        seen_imports = set()
        for imp in imports:
            if imp in seen_imports:
                warnings.append({
                    "principle": "no_redundancy",
                    "severity": "info",
                    "line": 0,
                    "message": f"Import duplicado: {imp}"
                })
            seen_imports.add(imp)
        
        return warnings


# ============================================
# Extended Code Indexer
# ============================================

class ExtendedKnowledgeIndexer:
    """
    Indexador extendido que conoce más que funciones y clases.
    
    Extiende el conocimiento del MCP para incluir:
    - Constantes y configuraciones
    - APIs y endpoints
    - Modelos de datos
    - Patrones de diseño
    - Documentación y TODOs
    - Dependencias entre módulos
    """
    
    # Patrones para detectar frameworks
    FRAMEWORK_PATTERNS = {
        "django": {
            "urls": r'path\s*\(\s*[\'"][^"\']+[\'"]\s*,',
            "views": r'def\s+\w+\s*\(\s*request',
            "models": r'class\s+\w+\s*\(\s*models\.Model\s*\)',
        },
        "flask": {
            "routes": r'@\w+\.route\s*\(\s*[\'"][^"\']+[\'"]',
            "methods": r'methods\s*=\s*\[',
        },
        "fastapi": {
            "routes": r'@\w+\.(get|post|put|delete|patch)\s*\(\s*[\'"][^"\']+[\'"]',
            "endpoints": r'async\s+def\s+\w+',
        }
    }
    
    # Patrones de diseño conocidos
    DESIGN_PATTERNS = {
        "singleton": [
            r'_instance\s*=\s*None',
            r'def\s+get_instance',
            r'if\s+cls\._instance\s+is\s+None'
        ],
        "factory": [
            r'def\s+create_',
            r'class\s+\w+Factory',
        ],
        "observer": [
            r'\.subscribe\s*\(',
            r'\.notify\s*\(',
            r'observers\s*=\s*\[\]',
        ],
        "decorator": [
            r'def\s+\w+\s*\(\s*func\s*\)',
            r'@functools\.wraps',
        ]
    }
    
    def __init__(self, index_dir: str = "data/extended_knowledge"):
        """Inicializar el indexador extendido"""
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Índices
        self.constants: Dict[str, ConstantInfo] = {}
        self.endpoints: Dict[str, APIEndpointInfo] = {}
        self.models: Dict[str, ModelInfo] = {}
        self.patterns: Dict[str, PatternInfo] = {}
        self.todos: List[TodoItem] = []
        self.dependencies: List[DependencyInfo] = []
        self.project_structure: Dict[str, Any] = {}
        
        # Quality Guardian siempre activo
        self.quality_guardian = QualityGuardian()
        
        logger.info(f"ExtendedKnowledgeIndexer initialized: {self.index_dir}")
    
    def index_file_extended(self, file_path: str) -> Dict[str, int]:
        """
        Indexar un archivo con conocimiento extendido.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Estadísticas de lo indexado
        """
        stats = {
            "constants": 0,
            "endpoints": 0,
            "models": 0,
            "patterns": 0,
            "todos": 0
        }
        
        try:
            path = Path(file_path)
            if not path.exists():
                return stats
            
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            module_name = path.stem
            
            # 1. Extraer constantes
            constants = self._extract_constants(source, module_name)
            for c in constants:
                key = f"{module_name}.{c.name}"
                self.constants[key] = c
                stats["constants"] += 1
            
            # 2. Extraer endpoints/APIs
            endpoints = self._extract_endpoints(source, module_name, str(path))
            for e in endpoints:
                key = f"{e.method}:{e.path}"
                self.endpoints[key] = e
                stats["endpoints"] += 1
            
            # 3. Detectar modelos
            models = self._extract_models(source, module_name)
            for m in models:
                key = f"{module_name}.{m.name}"
                self.models[key] = m
                stats["models"] += 1
            
            # 4. Detectar patrones de diseño
            patterns = self._detect_patterns(source, module_name)
            for p in patterns:
                key = f"{module_name}.{p.pattern_name}"
                self.patterns[key] = p
                stats["patterns"] += 1
            
            # 5. Extraer TODOs/FIXMEs
            todos = self._extract_todos(source, module_name)
            self.todos.extend(todos)
            stats["todos"] += len(todos)
            
            # 6. Extraer dependencias
            deps = self._extract_dependencies(source, module_name)
            self.dependencies.extend(deps)
            
            logger.info(f"Extended index for {module_name}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in extended indexing of {file_path}: {e}")
            return stats
    
    def _extract_constants(self, source: str, module: str) -> List[ConstantInfo]:
        """Extraer constantes y variables globales"""
        constants = []
        
        try:
            tree = ast.parse(source)
            
            for node in ast.iter_child_nodes(tree):
                # Asignaciones a nivel de módulo
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            name = target.id
                            # Detectar constantes (MAYÚSCULAS) o configuraciones
                            is_constant = name.isupper()
                            is_config = any(kw in name.lower() for kw in 
                                          ['config', 'setting', 'option', 'default'])
                            
                            if is_constant or is_config:
                                value_preview = ast.unparse(node.value)[:100]
                                constants.append(ConstantInfo(
                                    name=name,
                                    module=module,
                                    value_type=type(node.value).__name__,
                                    value_preview=value_preview,
                                    line=node.lineno,
                                    is_configuration=is_config
                                ))
        except Exception as e:
            logger.warning(f"Error extracting constants: {e}")
        
        return constants
    
    def _extract_endpoints(self, source: str, module: str, file_path: str) -> List[APIEndpointInfo]:
        """Extraer endpoints de APIs (Django, Flask, FastAPI)"""
        endpoints = []
        
        # Detectar framework
        framework = None
        for fw, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern_name, pattern in patterns.items():
                if re.search(pattern, source):
                    framework = fw
                    break
            if framework:
                break
        
        if not framework:
            return endpoints
        
        try:
            if framework == "django":
                # Buscar urlpatterns
                url_pattern = r'path\s*\(\s*[\'"]([^"\']+)[\'"]\s*,\s*(\w+)'
                for match in re.finditer(url_pattern, source):
                    endpoints.append(APIEndpointInfo(
                        path=match.group(1),
                        method="ANY",
                        function_name=match.group(2),
                        module=module,
                        line=source[:match.start()].count('\n') + 1,
                        framework="django"
                    ))
            
            elif framework == "flask":
                # Buscar decoradores @app.route
                route_pattern = r'@(\w+)\.route\s*\(\s*[\'"]([^"\']+)[\'"](?:.*?methods\s*=\s*\[([^\]]+)\])?'
                for match in re.finditer(route_pattern, source, re.DOTALL):
                    methods = match.group(3) or "GET"
                    endpoints.append(APIEndpointInfo(
                        path=match.group(2),
                        method=methods.replace("'", "").replace('"', '').strip(),
                        function_name="",
                        module=module,
                        line=source[:match.start()].count('\n') + 1,
                        framework="flask"
                    ))
            
            elif framework == "fastapi":
                # Buscar decoradores @app.get, @app.post, etc.
                route_pattern = r'@(\w+)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^"\']+)[\'"]'
                for match in re.finditer(route_pattern, source):
                    endpoints.append(APIEndpointInfo(
                        path=match.group(3),
                        method=match.group(2).upper(),
                        function_name="",
                        module=module,
                        line=source[:match.start()].count('\n') + 1,
                        framework="fastapi"
                    ))
                    
        except Exception as e:
            logger.warning(f"Error extracting endpoints: {e}")
        
        return endpoints
    
    def _extract_models(self, source: str, module: str) -> List[ModelInfo]:
        """Extraer modelos de datos"""
        models = []
        
        try:
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    model_type = None
                    fields = []
                    
                    # Detectar tipo de modelo
                    for base in node.bases:
                        base_name = ast.unparse(base)
                        if 'Model' in base_name:
                            model_type = 'django'
                        elif 'BaseModel' in base_name:
                            model_type = 'pydantic'
                        elif 'Base' in base_name:
                            model_type = 'sqlalchemy'
                    
                    # Detectar dataclass
                    for dec in node.decorator_list:
                        if 'dataclass' in ast.unparse(dec):
                            model_type = 'dataclass'
                    
                    if model_type:
                        # Extraer campos
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign):
                                field_name = item.target.id if isinstance(item.target, ast.Name) else ""
                                field_type = ast.unparse(item.annotation) if item.annotation else "Any"
                                fields.append({
                                    "name": field_name,
                                    "type": field_type
                                })
                        
                        models.append(ModelInfo(
                            name=node.name,
                            module=module,
                            model_type=model_type,
                            fields=fields,
                            line=node.lineno,
                            docstring=ast.get_docstring(node)
                        ))
                        
        except Exception as e:
            logger.warning(f"Error extracting models: {e}")
        
        return models
    
    def _detect_patterns(self, source: str, module: str) -> List[PatternInfo]:
        """Detectar patrones de diseño en el código"""
        patterns = []
        
        for pattern_name, indicators in self.DESIGN_PATTERNS.items():
            matches = 0
            evidence_lines = []
            
            for indicator in indicators:
                if re.search(indicator, source):
                    matches += 1
                    evidence_lines.append(indicator)
            
            if matches >= 2:  # Al menos 2 indicadores
                confidence = min(1.0, matches / len(indicators))
                patterns.append(PatternInfo(
                    pattern_name=pattern_name,
                    module=module,
                    class_name=None,
                    confidence=confidence,
                    evidence=", ".join(evidence_lines[:3])
                ))
        
        return patterns
    
    def _extract_todos(self, source: str, module: str) -> List[TodoItem]:
        """Extraer TODOs, FIXMEs, HACKs del código"""
        todos = []
        
        patterns = {
            "TODO": (r'#\s*TODO[:\s]+(.+)$', "medium"),
            "FIXME": (r'#\s*FIXME[:\s]+(.+)$', "high"),
            "HACK": (r'#\s*HACK[:\s]+(.+)$', "high"),
            "NOTE": (r'#\s*NOTE[:\s]+(.+)$', "low"),
            "XXX": (r'#\s*XXX[:\s]+(.+)$', "high"),
        }
        
        lines = source.split('\n')
        for i, line in enumerate(lines):
            for todo_type, (pattern, priority) in patterns.items():
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    todos.append(TodoItem(
                        type=todo_type,
                        text=match.group(1).strip(),
                        module=module,
                        line=i + 1,
                        priority=priority
                    ))
        
        return todos
    
    def _extract_dependencies(self, source: str, module: str) -> List[DependencyInfo]:
        """Extraer dependencias entre módulos"""
        dependencies = []
        
        try:
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(DependencyInfo(
                            source_module=module,
                            target_module=alias.name,
                            import_type="direct",
                            items_imported=[]
                        ))
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        items = [alias.name for alias in node.names]
                        dependencies.append(DependencyInfo(
                            source_module=module,
                            target_module=node.module,
                            import_type="from",
                            items_imported=items
                        ))
                        
        except Exception as e:
            logger.warning(f"Error extracting dependencies: {e}")
        
        return dependencies
    
    def index_directory_extended(self, directory: str, recursive: bool = True) -> Dict[str, int]:
        """Indexar directorio completo con conocimiento extendido"""
        total_stats = {
            "files": 0,
            "constants": 0,
            "endpoints": 0,
            "models": 0,
            "patterns": 0,
            "todos": 0
        }
        
        exclude_dirs = {'venv', 'node_modules', '.git', '__pycache__', 'migrations'}
        path = Path(directory)
        
        pattern = '**/*.py' if recursive else '*.py'
        for py_file in path.glob(pattern):
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue
            
            stats = self.index_file_extended(str(py_file))
            total_stats["files"] += 1
            for key in stats:
                total_stats[key] += stats[key]
        
        # Construir estructura del proyecto
        self.project_structure = self._build_project_structure(directory)
        
        logger.info(f"Extended indexing complete: {total_stats}")
        return total_stats
    
    def _build_project_structure(self, directory: str) -> Dict[str, Any]:
        """Construir estructura del proyecto"""
        structure = {
            "root": directory,
            "apps": [],
            "core_modules": [],
            "config_files": [],
            "test_modules": []
        }
        
        path = Path(directory)
        
        for item in path.rglob('*'):
            if item.is_file():
                rel_path = str(item.relative_to(path))
                if item.suffix == '.py':
                    if 'test' in item.stem.lower():
                        structure["test_modules"].append(rel_path)
                    elif item.stem in ['settings', 'config', 'urls', 'models', 'views']:
                        structure["core_modules"].append(rel_path)
                elif item.suffix in ['.json', '.yaml', '.yml', '.env', '.ini']:
                    structure["config_files"].append(rel_path)
        
        return structure
    
    def get_quality_reminder(self) -> str:
        """Obtener recordatorio de calidad para inyectar en respuestas"""
        return self.quality_guardian.get_reminder()
    
    def check_code_quality(self, code: str) -> List[Dict[str, Any]]:
        """Verificar calidad del código"""
        return self.quality_guardian.check_code_quality(code)
    
    def save_index(self) -> None:
        """Guardar índice extendido a disco"""
        data = {
            "constants": {k: asdict(v) for k, v in self.constants.items()},
            "endpoints": {k: asdict(v) for k, v in self.endpoints.items()},
            "models": {k: asdict(v) for k, v in self.models.items()},
            "patterns": {k: asdict(v) for k, v in self.patterns.items()},
            "todos": [asdict(t) for t in self.todos],
            "dependencies": [asdict(d) for d in self.dependencies],
            "project_structure": self.project_structure,
            "last_indexed": datetime.now().isoformat()
        }
        
        with open(self.index_dir / 'extended_index.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Extended index saved to {self.index_dir}")
    
    def load_index(self) -> bool:
        """Cargar índice extendido desde disco"""
        try:
            index_file = self.index_dir / 'extended_index.json'
            if not index_file.exists():
                return False
            
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.constants = {k: ConstantInfo(**v) for k, v in data.get("constants", {}).items()}
            self.endpoints = {k: APIEndpointInfo(**v) for k, v in data.get("endpoints", {}).items()}
            self.models = {k: ModelInfo(**v) for k, v in data.get("models", {}).items()}
            self.patterns = {k: PatternInfo(**v) for k, v in data.get("patterns", {}).items()}
            self.todos = [TodoItem(**t) for t in data.get("todos", [])]
            self.dependencies = [DependencyInfo(**d) for d in data.get("dependencies", [])]
            self.project_structure = data.get("project_structure", {})
            
            logger.info("Extended index loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading extended index: {e}")
            return False
    
    def get_knowledge_summary(self) -> str:
        """Obtener resumen del conocimiento extendido"""
        summary = "# 🧠 Extended Knowledge Summary\n\n"
        
        summary += f"## 📊 Statistics\n"
        summary += f"- Constants/Configs: {len(self.constants)}\n"
        summary += f"- API Endpoints: {len(self.endpoints)}\n"
        summary += f"- Data Models: {len(self.models)}\n"
        summary += f"- Design Patterns: {len(self.patterns)}\n"
        summary += f"- TODOs/FIXMEs: {len(self.todos)}\n"
        summary += f"- Dependencies: {len(self.dependencies)}\n\n"
        
        if self.endpoints:
            summary += "## 🌐 API Endpoints\n"
            for key, endpoint in list(self.endpoints.items())[:10]:
                summary += f"- `{endpoint.method} {endpoint.path}` ({endpoint.framework})\n"
            if len(self.endpoints) > 10:
                summary += f"  ... and {len(self.endpoints) - 10} more\n"
            summary += "\n"
        
        if self.models:
            summary += "## 📦 Data Models\n"
            for key, model in list(self.models.items())[:10]:
                summary += f"- `{model.name}` ({model.model_type}) - {len(model.fields)} fields\n"
            summary += "\n"
        
        if self.patterns:
            summary += "## 🎨 Design Patterns Detected\n"
            for key, pattern in self.patterns.items():
                summary += f"- {pattern.pattern_name.title()} in `{pattern.module}` (confidence: {pattern.confidence:.0%})\n"
            summary += "\n"
        
        if self.todos:
            high_priority = [t for t in self.todos if t.priority == "high"]
            if high_priority:
                summary += "## ⚠️ High Priority TODOs\n"
                for todo in high_priority[:5]:
                    summary += f"- [{todo.type}] {todo.text} ({todo.module}:{todo.line})\n"
                summary += "\n"
        
        # Siempre incluir Quality Guardian
        summary += self.quality_guardian.get_reminder()
        
        return summary
    
    def search_extended(self, query: str) -> List[Dict[str, Any]]:
        """Buscar en el conocimiento extendido"""
        results = []
        query_lower = query.lower()
        
        # Buscar en constantes
        for key, const in self.constants.items():
            if query_lower in const.name.lower():
                results.append({
                    "type": "constant",
                    "name": const.name,
                    "module": const.module,
                    "value": const.value_preview,
                    "line": const.line
                })
        
        # Buscar en endpoints
        for key, endpoint in self.endpoints.items():
            if query_lower in endpoint.path.lower() or query_lower in endpoint.function_name.lower():
                results.append({
                    "type": "endpoint",
                    "path": endpoint.path,
                    "method": endpoint.method,
                    "module": endpoint.module,
                    "framework": endpoint.framework
                })
        
        # Buscar en modelos
        for key, model in self.models.items():
            if query_lower in model.name.lower():
                results.append({
                    "type": "model",
                    "name": model.name,
                    "model_type": model.model_type,
                    "fields": len(model.fields),
                    "module": model.module
                })
        
        return results


# ============================================
# Factory functions
# ============================================

_extended_indexer = None
_quality_guardian = None

def get_extended_indexer() -> ExtendedKnowledgeIndexer:
    """Obtener instancia singleton del indexador extendido"""
    global _extended_indexer
    if _extended_indexer is None:
        _extended_indexer = ExtendedKnowledgeIndexer()
    return _extended_indexer

def get_quality_guardian() -> QualityGuardian:
    """Obtener instancia singleton del Quality Guardian"""
    global _quality_guardian
    if _quality_guardian is None:
        _quality_guardian = QualityGuardian()
    return _quality_guardian
