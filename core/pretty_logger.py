"""
Pretty Logger - Beautiful Console Logging for MCP Hub v8
=========================================================

Sistema de logging con formato bonito y colores para mejor
visualización de las operaciones del MCP.

Features:
- Colores en consola (Windows compatible)
- Emojis para identificar tipo de mensaje
- Formato estructurado y legible
- Niveles: DEBUG, INFO, WARNING, ERROR, SUCCESS
- Contexto adicional con metadatos
"""

import sys
import logging
import random
from datetime import datetime
from typing import Optional, Dict, Any, Union
from enum import Enum
from pathlib import Path
import json

# ============================================
# Colores para Windows
# ============================================

# Habilitar colores ANSI en Windows
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


class Colors:
    """Códigos de color ANSI"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    
    # Colores de texto
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Colores brillantes
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Tonos Verdes Especiales para Yari (Branding)
    GREEN_PALE = "\033[38;5;120m"
    GREEN_MID = "\033[38;5;114m"
    GREEN_DARK = "\033[38;5;108m"
    GREEN_NEON = "\033[38;5;82m"
    GREEN_MINT = "\033[38;5;158m"
    
    # Fondos
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_YARI = "\033[48;5;22m" # Fondo verde oscuro


class LogLevel(Enum):
    """Niveles de log con emojis y colores"""
    DEBUG = ("🔍", Colors.BRIGHT_BLACK, "DEBUG")
    INFO = ("ℹ️ ", Colors.BRIGHT_BLUE, "INFO")
    SUCCESS = ("✅", Colors.BRIGHT_GREEN, "SUCCESS")
    WARNING = ("⚠️ ", Colors.BRIGHT_YELLOW, "WARNING")
    ERROR = ("❌", Colors.BRIGHT_RED, "ERROR")
    CRITICAL = ("🔥", Colors.RED + Colors.BOLD, "CRITICAL")
    
    # Tipos especiales para MCP v9
    TOOL = ("🔧", Colors.BRIGHT_CYAN, "TOOL")
    SESSION = ("📁", Colors.BRIGHT_MAGENTA, "SESSION")
    INDEX = ("📊", Colors.BRIGHT_GREEN, "INDEX")
    QUERY = ("🔎", Colors.BRIGHT_BLUE, "QUERY")
    QUALITY = ("🛡️ ", Colors.BRIGHT_YELLOW, "QUALITY")
    GROUNDING = ("🌍", Colors.GREEN_MINT, "GROUND")
    MEMORY = ("🧠", Colors.MAGENTA, "MEMORY")
    SKILL = ("📜", Colors.GREEN_PALE, "SKILL")
    V9_FLOW = ("🔄", Colors.GREEN_NEON, "V9-FLOW")


# ============================================
# Pretty Logger Class
# ============================================

class PrettyLogger:
    """
    Logger bonito para MCP Hub.
    
    Uso:
        from pretty_logger import logger
        
        logger.info("Servidor iniciado", port=8765)
        logger.success("Sesión creada", session_id="mi-proyecto")
        logger.tool("get_context", query="buscar algo")
        logger.quality("Código analizado", warnings=3)
    """
    
    def __init__(
        self,
        name: str = "MCP",
        log_file: Optional[str] = None,
        level: str = "DEBUG",
        show_timestamp: bool = True,
        show_module: bool = True,
        use_colors: bool = True
    ):
        """
        Inicializar logger.
        
        Args:
            name: Nombre del logger
            log_file: Archivo para guardar logs (opcional)
            level: Nivel mínimo de log
            show_timestamp: Mostrar timestamp en cada mensaje
            show_module: Mostrar nombre del módulo
            use_colors: Usar colores en consola
        """
        self.name = name
        self.log_file = log_file
        self.show_timestamp = show_timestamp
        self.show_module = show_module
        self.use_colors = use_colors
        
        # Configurar archivo de log si se especifica
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_handler = open(log_path, 'a', encoding='utf-8')
        else:
            self._file_handler = None
        
        # Estadísticas
        self._stats = {
            "debug": 0,
            "info": 0,
            "success": 0,
            "warning": 0,
            "error": 0,
            "critical": 0
        }
    
    def _format_message(
        self,
        level: LogLevel,
        message: str,
        module: Optional[str] = None,
        **kwargs
    ) -> tuple:
        """Formatear mensaje para consola y archivo"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        emoji, color, level_name = level.value
        
        # Construir mensaje para consola (con colores)
        console_parts = []
        
        if self.show_timestamp:
            console_parts.append(f"{Colors.DIM}{timestamp}{Colors.RESET}")
        
        console_parts.append(f"{color}{emoji} {level_name:8}{Colors.RESET}")
        
        if self.show_module and module:
            console_parts.append(f"{Colors.DIM}[{module}]{Colors.RESET}")
        
        console_parts.append(message)
        
        # Agregar kwargs como contexto
        if kwargs:
            context_str = " | ".join(f"{Colors.CYAN}{k}{Colors.RESET}={v}" for k, v in kwargs.items())
            console_parts.append(f"{Colors.DIM}({context_str}){Colors.RESET}")
        
        console_msg = " ".join(console_parts)
        
        # Construir mensaje para archivo (sin colores)
        file_parts = [f"[{timestamp}]", f"[{level_name}]"]
        if module:
            file_parts.append(f"[{module}]")
        file_parts.append(message)
        if kwargs:
            file_parts.append(str(kwargs))
        file_msg = " ".join(file_parts)
        
        return console_msg, file_msg
    
    def _log(self, level: LogLevel, message: str, module: Optional[str] = None, **kwargs):
        """Log interno"""
        console_msg, file_msg = self._format_message(level, message, module, **kwargs)
        
        # Print a consola
        if self.use_colors:
            print(console_msg, file=sys.stderr)
        else:
            print(file_msg, file=sys.stderr)
        
        # Escribir a archivo
        if self._file_handler:
            self._file_handler.write(file_msg + "\n")
            self._file_handler.flush()
        
        # Actualizar estadísticas
        level_key = level.name.lower()
        if level_key in self._stats:
            self._stats[level_key] += 1
    
    # ============================================
    # Métodos de logging estándar
    # ============================================
    
    def debug(self, message: str, **kwargs):
        """Log de nivel DEBUG"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de nivel INFO"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log de nivel SUCCESS (operación exitosa)"""
        self._log(LogLevel.SUCCESS, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de nivel WARNING"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de nivel ERROR"""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log de nivel CRITICAL"""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    # ============================================
    # Métodos específicos de MCP
    # ============================================
    
    def tool(self, tool_name: str, **kwargs):
        """Log de ejecución de tool MCP"""
        self._log(LogLevel.TOOL, f"Executing: {tool_name}", **kwargs)
    
    def tool_result(self, tool_name: str, success: bool = True, **kwargs):
        """Log de resultado de tool MCP"""
        if success:
            self._log(LogLevel.SUCCESS, f"Tool completed: {tool_name}", **kwargs)
        else:
            self._log(LogLevel.ERROR, f"Tool failed: {tool_name}", **kwargs)
    
    def session(self, action: str, session_id: str, **kwargs):
        """Log de operaciones de sesión"""
        self._log(LogLevel.SESSION, f"{action}: {session_id}", **kwargs)
    
    def index(self, message: str, **kwargs):
        """Log de operaciones de indexación"""
        self._log(LogLevel.INDEX, message, **kwargs)
    
    def query(self, query: str, results: int = 0, **kwargs):
        """Log de consultas"""
        self._log(LogLevel.QUERY, f"Query: {query[:50]}...", results=results, **kwargs)
    
    def quality(self, message: str, **kwargs):
        """Log de Quality Guardian"""
        self._log(LogLevel.QUALITY, message, **kwargs)
    
    # ============================================
    # Utilidades
    # ============================================
    
    def divider(self, title: str = "", char: str = "═", width: int = 60):
        """Imprimir línea divisoria"""
        if title:
            title_part = f" {title} "
            padding = (width - len(title_part)) // 2
            line = char * padding + title_part + char * padding
        else:
            line = char * width
        
        print(f"{Colors.DIM}{line}{Colors.RESET}", file=sys.stderr)
    
    def header(self, title: str, subtitle: str = ""):
        """Imprimir encabezado bonito con branding ASCII"""
        self.divider("", char="━", width=80)
        
        # ASCII Art para Context Vortex
        ascii_art = f"""
{Colors.GREEN_NEON}  ██████╗ ██████╗ ███╗   ██╗████████╗███████╗██╗  ██╗████████╗
{Colors.GREEN_PALE} ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝╚██╗██╔╝╚══██╔══╝
{Colors.GREEN_MID} ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗   ╚███╔╝    ██║   
{Colors.GREEN_DARK} ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝   ██╔██╗    ██║   
{Colors.GREEN_NEON} ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗██╔╝ ██╗   ██║   
{Colors.BRIGHT_BLACK}  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝   ╚═╝   
{Colors.CYAN}       ██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
{Colors.CYAN}       ██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
{Colors.CYAN}       ██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
{Colors.CYAN}       ╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
{Colors.CYAN}        ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
{Colors.CYAN}         ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
        """
        print(ascii_art, file=sys.stderr)
        
        print(f"  {Colors.BOLD}{Colors.GREEN_NEON}✨ {title}{Colors.RESET}", file=sys.stderr)
        if subtitle:
            print(f"  {Colors.DIM}{Colors.GREEN_MINT}🚀 {subtitle}{Colors.RESET}", file=sys.stderr)
        
        self.divider(f" v9 Contextual Intelligence Core ", char="━", width=80)
        print(f"  {Colors.DIM}System Status: {Colors.GREEN_PALE}ONLINE{Colors.RESET} | {Colors.DIM}Anti-Hallucination: {Colors.GREEN_PALE}ACTIVE{Colors.RESET}", file=sys.stderr)
        self.divider("", char="─", width=80)

    def v9_flow(self, step: str, details: str = ""):
        """Log específico para ver el flujo de datos interactivo"""
        self._log(LogLevel.V9_FLOW, f"{Colors.BOLD}{step}{Colors.RESET} -> {details}")

    def matrix_flow(self, tool_name: str, action: str, color: str = Colors.GREEN_NEON):
        """Matrix-like visual flow for tools with binary/ASCII patterns"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Generar "lluvia de datos" binarios (3 líneas para efecto visual)
        binary_chars = "01 "
        ascii_chars = ".:-=+*#%@"
        
        rain_lines = []
        for _ in range(3):
            p = "".join(random.choice(binary_chars) for _ in range(12))
            s = "".join(random.choice(ascii_chars) for _ in range(12))
            rain_lines.append((p, s))
        
        # Línea de acción principal centrada entre lluvia
        print(f"{Colors.DIM}{timestamp}{Colors.RESET} {color}{rain_lines[0][0]}                     {rain_lines[0][1]}{Colors.RESET}", file=sys.stderr)
        
        matrix_msg = f"{Colors.DIM}{timestamp}{Colors.RESET} {color}{Colors.BOLD}【 {rain_lines[1][0]} 】{Colors.RESET} "
        matrix_msg += f"{color}{action.upper()}{Colors.RESET}: {Colors.BOLD}{tool_name}{Colors.RESET} "
        matrix_msg += f"{color}{Colors.BOLD}【 {rain_lines[1][1]} 】{Colors.RESET}"
        print(matrix_msg, file=sys.stderr)
        
        print(f"{Colors.DIM}{timestamp}{Colors.RESET} {color}{rain_lines[2][0]}                     {rain_lines[2][1]}{Colors.RESET}", file=sys.stderr)
        
        # Escribir a archivo si existe
        if self._file_handler:
            self._file_handler.write(f"[{timestamp}] [MATRIX] {action}: {tool_name}\n")
            self._file_handler.flush()
    
    def json(self, data: Union[Dict, list], title: str = "Data"):
        """Imprimir JSON formateado"""
        print(f"{Colors.DIM}─── {title} ───{Colors.RESET}", file=sys.stderr)
        formatted = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        for line in formatted.split('\n'):
            print(f"{Colors.CYAN}{line}{Colors.RESET}", file=sys.stderr)
    
    def stats(self) -> Dict[str, int]:
        """Obtener estadísticas de logs"""
        return self._stats.copy()
    
    def print_stats(self):
        """Imprimir estadísticas de logs"""
        self.divider("Log Statistics")
        for level, count in self._stats.items():
            if count > 0:
                print(f"  {level.upper():10} : {count}", file=sys.stderr)
        self.divider()
    
    def close(self):
        """Cerrar archivo de log si existe"""
        if self._file_handler:
            self._file_handler.close()


# ============================================
# Logger Handler para integrar con logging estándar
# ============================================

class PrettyHandler(logging.Handler):
    """Handler para integrar PrettyLogger con logging estándar de Python"""
    
    def __init__(self, pretty_logger: PrettyLogger):
        super().__init__()
        self.pretty_logger = pretty_logger
    
    def emit(self, record: logging.LogRecord):
        try:
            level_map = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.CRITICAL
            }
            
            level = level_map.get(record.levelno, LogLevel.INFO)
            message = self.format(record)
            
            self.pretty_logger._log(level, message, module=record.name)
        except Exception:
            self.handleError(record)


# ============================================
# Instancia global (singleton)
# ============================================

# Logger global para uso fácil
_logger_instance = None

def get_logger(
    name: str = "MCP",
    log_file: Optional[str] = "logs/mcp_pretty.log"
) -> PrettyLogger:
    """Obtener instancia singleton del logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PrettyLogger(name=name, log_file=log_file)
    return _logger_instance

# Alias convenientes
logger = get_logger()


def configure_standard_logging(level: int = logging.DEBUG):
    """
    Configurar logging estándar de Python para usar PrettyLogger.
    
    Uso:
        from pretty_logger import configure_standard_logging
        configure_standard_logging()
        
        import logging
        logging.info("Este mensaje será bonito!")
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Agregar PrettyHandler
    pretty_handler = PrettyHandler(get_logger())
    pretty_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(pretty_handler)


# ============================================
# Demo/Test
# ============================================

if __name__ == "__main__":
    # Demo del logger
    log = get_logger()
    
    log.header("MCP Hub v8", "Pretty Logger Demo")
    
    log.debug("Este es un mensaje de debug", extra="info")
    log.info("Servidor iniciando", port=8765, host="127.0.0.1")
    log.success("Conexión establecida", client="Antigravity")
    log.warning("Memoria alta", usage="85%")
    log.error("Error de conexión", code=500)
    log.critical("Sistema crítico!", reason="Out of memory")
    
    log.divider("MCP Operations")
    
    log.tool("get_context", query="buscar autenticación")
    log.session("Created", "mi-proyecto-feature-0115")
    log.index("Indexed 42 files", functions=156, classes=23)
    log.query("cómo funciona el login", results=5)
    log.quality("Código analizado", warnings=2, issues=["duplication", "long_function"])
    
    log.divider()
    
    log.json({
        "session": "active",
        "tools": 24,
        "indexed_files": 42
    }, title="System Status")
    
    log.print_stats()
