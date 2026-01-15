"""
Code Indexer - Extract Structure from Source Code
AST-based indexing for Python code (extensible to other languages)
"""

import ast
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Information about a function"""
    name: str
    module: str
    signature: str
    line_start: int
    line_end: int
    docstring: Optional[str]
    parameters: List[str]
    returns: Optional[str]
    decorators: List[str]
    calls: List[str]  # Functions called within this function


@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    module: str
    line_start: int
    line_end: int
    docstring: Optional[str]
    methods: List[str]
    bases: List[str]
    decorators: List[str]


@dataclass
class ModuleInfo:
    """Information about a module"""
    name: str
    file_path: str
    imports: List[str]
    functions: List[str]
    classes: List[str]
    last_indexed: str


class CodeIndexer:
    """
    Index code structure from Python files
    
    Features:
    - Extract functions, classes, methods
    - Parse signatures and docstrings
    - Track dependencies (imports, function calls)
    - Build module dependency graph
    """
    
    def __init__(self, index_dir: str = "data/code_index"):
        """
        Initialize code indexer
        
        Args:
            index_dir: Directory to store index files
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.functions: Dict[str, FunctionInfo] = {}
        self.classes: Dict[str, ClassInfo] = {}
        self.modules: Dict[str, ModuleInfo] = {}
        
        logger.info(f"CodeIndexer initialized: {self.index_dir}")
    
    def index_file(self, file_path: str) -> bool:
        """
        Index a single Python file
        
        Args:
            file_path: Path to Python file
            
        Returns:
            True if indexed successfully
        """
        try:
            path = Path(file_path)
            if not path.exists() or path.suffix != '.py':
                logger.warning(f"Skipping non-Python file: {file_path}")
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(path))
            module_name = path.stem
            
            # Extract module-level info
            imports = self._extract_imports(tree)
            
            # Extract functions and classes
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self._extract_function_info(node, module_name, source)
                    if func_info:
                        func_key = f"{module_name}.{func_info.name}"
                        self.functions[func_key] = func_info
                        functions.append(func_info.name)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, module_name, source)
                    if class_info:
                        class_key = f"{module_name}.{class_info.name}"
                        self.classes[class_key] = class_info
                        classes.append(class_info.name)
            
            # Store module info
            module_info = ModuleInfo(
                name=module_name,
                file_path=str(path),
                imports=imports,
                functions=functions,
                classes=classes,
                last_indexed=datetime.now().isoformat()
            )
            self.modules[module_name] = module_info
            
            logger.info(
                f"Indexed {module_name}: "
                f"{len(functions)} functions, {len(classes)} classes"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
            return False
    
    def index_directory(
        self,
        directory: str,
        recursive: bool = True,
        exclude_dirs: Optional[Set[str]] = None
    ) -> int:
        """
        Index all Python files in a directory
        
        Args:
            directory: Directory to index
            recursive: Recursively index subdirectories
            exclude_dirs: Set of directory names to exclude
            
        Returns:
            Number of files indexed
        """
        exclude_dirs = exclude_dirs or {'venv', 'node_modules', '.git', '__pycache__'}
        path = Path(directory)
        indexed_count = 0
        
        if recursive:
            for py_file in path.rglob('*.py'):
                # Check if file is in excluded directory
                if any(excluded in py_file.parts for excluded in exclude_dirs):
                    continue
                
                if self.index_file(str(py_file)):
                    indexed_count += 1
        else:
            for py_file in path.glob('*.py'):
                if self.index_file(str(py_file)):
                    indexed_count += 1
        
        logger.info(f"Indexed {indexed_count} files from {directory}")
        return indexed_count
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return list(set(imports))  # Deduplicate
    
    def _extract_function_info(
        self,
        node: ast.FunctionDef,
        module: str,
        source: str
    ) -> Optional[FunctionInfo]:
        """Extract information from a function node"""
        try:
            # Get signature
            args = [arg.arg for arg in node.args.args]
            signature = f"{node.name}({', '.join(args)})"
            
            # Get return type if annotated
            returns = None
            if node.returns:
                returns = ast.unparse(node.returns)
            
            # Get docstring
            docstring = ast.get_docstring(node)
            
            # Get decorators
            decorators = [ast.unparse(dec) for dec in node.decorator_list]
            
            # Extract function calls
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        calls.append(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        calls.append(child.func.attr)
            
            return FunctionInfo(
                name=node.name,
                module=module,
                signature=signature,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                docstring=docstring,
                parameters=args,
                returns=returns,
                decorators=decorators,
                calls=list(set(calls))
            )
        except Exception as e:
            logger.warning(f"Error extracting function {node.name}: {e}")
            return None
    
    def _extract_class_info(
        self,
        node: ast.ClassDef,
        module: str,
        source: str
    ) -> Optional[ClassInfo]:
        """Extract information from a class node"""
        try:
            # Get methods
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
            
            # Get base classes
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
            
            # Get decorators
            decorators = [ast.unparse(dec) for dec in node.decorator_list]
            
            # Get docstring
            docstring = ast.get_docstring(node)
            
            return ClassInfo(
                name=node.name,
                module=module,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                docstring=docstring,
                methods=methods,
                bases=bases,
                decorators=decorators
            )
        except Exception as e:
            logger.warning(f"Error extracting class {node.name}: {e}")
            return None
    
    def search_function(self, name: str) -> List[FunctionInfo]:
        """
        Search for functions by name (partial match)
        
        Args:
            name: Function name to search for
            
        Returns:
            List of matching FunctionInfo objects
        """
        name_lower = name.lower()
        matches = []
        
        for func_key, func_info in self.functions.items():
            if name_lower in func_info.name.lower():
                matches.append(func_info)
        
        return matches
    
    def search_class(self, name: str) -> List[ClassInfo]:
        """
        Search for classes by name (partial match)
        
        Args:
            name: Class name to search for
            
        Returns:
            List of matching ClassInfo objects
        """
        name_lower = name.lower()
        matches = []
        
        for class_key, class_info in self.classes.items():
            if name_lower in class_info.name.lower():
                matches.append(class_info)
        
        return matches
    
    def get_function_location(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get location of a function
        
        Args:
            name: Function name
            
        Returns:
            Dict with module, file, line info or None
        """
        for func_key, func_info in self.functions.items():
            if func_info.name == name:
                module_info = self.modules.get(func_info.module)
                return {
                    'function': name,
                    'module': func_info.module,
                    'file': module_info.file_path if module_info else None,
                    'line_start': func_info.line_start,
                    'line_end': func_info.line_end,
                    'signature': func_info.signature
                }
        
        return None
    
    def save_index(self) -> None:
        """Save index to disk"""
        # Save functions
        functions_data = {k: asdict(v) for k, v in self.functions.items()}
        with open(self.index_dir / 'functions.json', 'w', encoding='utf-8') as f:
            json.dump(functions_data, f, indent=2, ensure_ascii=False)
        
        # Save classes
        classes_data = {k: asdict(v) for k, v in self.classes.items()}
        with open(self.index_dir / 'classes.json', 'w', encoding='utf-8') as f:
            json.dump(classes_data, f, indent=2, ensure_ascii=False)
        
        # Save modules
        modules_data = {k: asdict(v) for k, v in self.modules.items()}
        with open(self.index_dir / 'modules.json', 'w', encoding='utf-8') as f:
            json.dump(modules_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Index saved to {self.index_dir}")
    
    def load_index(self) -> bool:
        """
        Load index from disk
        
        Returns:
            True if loaded successfully
        """
        try:
            # Load functions
            functions_file = self.index_dir / 'functions.json'
            if functions_file.exists():
                with open(functions_file, 'r', encoding='utf-8') as f:
                    functions_data = json.load(f)
                    self.functions = {
                        k: FunctionInfo(**v) for k, v in functions_data.items()
                    }
            
            # Load classes
            classes_file = self.index_dir / 'classes.json'
            if classes_file.exists():
                with open(classes_file, 'r', encoding='utf-8') as f:
                    classes_data = json.load(f)
                    self.classes = {
                        k: ClassInfo(**v) for k, v in classes_data.items()
                    }
            
            # Load modules
            modules_file = self.index_dir / 'modules.json'
            if modules_file.exists():
                with open(modules_file, 'r', encoding='utf-8') as f:
                    modules_data = json.load(f)
                    self.modules = {
                        k: ModuleInfo(**v) for k, v in modules_data.items()
                    }
            
            logger.info(
                f"Index loaded: {len(self.functions)} functions, "
                f"{len(self.classes)} classes, {len(self.modules)} modules"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get indexing statistics"""
        return {
            'total_modules': len(self.modules),
            'total_functions': len(self.functions),
            'total_classes': len(self.classes)
        }
