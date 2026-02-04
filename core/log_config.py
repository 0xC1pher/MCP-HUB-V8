"""
Log Configuration - Clean & Beautiful Logging for MCP Hub v8
=============================================================

Este módulo configura un sistema de logging limpio y legible:
- Filtra el ruido de sse_starlette
- Formatea JSON de forma legible
- Silencia los pings repetitivos
- Muestra solo lo importante de forma bonita

Uso:
    from log_config import setup_clean_logging
    setup_clean_logging()
"""

import sys
import logging
import json
import re
from datetime import datetime
from typing import Optional

# ============================================
# Habilitar colores ANSI en Windows
# ============================================
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


# ============================================
# Colores ANSI
# ============================================
class C:
    """Códigos de color ANSI simplificados"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Colores
    GRAY = "\033[90m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


# ============================================
# Filtros de Log
# ============================================

class SSENoiseFilter(logging.Filter):
    """
    Filtra el ruido de sse_starlette y otros loggers ruidosos.
    
    Elimina:
    - Mensajes de ping (cada 15s, no aportan nada)
    - Bytes crudos de chunks SSE
    - Mensajes extremadamente largos
    """
    
    # Patrones a silenciar completamente
    SILENCE_PATTERNS = [
        r"ping:",                    # Pings periódicos
        r"ping -",                   # Pings con timestamp
        r"b': ping",                 # Bytes de ping
        r"chunk: b'",                # Chunks SSE crudos
        r"\\\\n",                    # Newlines escapados
        r"\{.*\"jsonrpc\".*\}",      # JSON-RPC completo
    ]
    
    # Compilar patrones para eficiencia
    _compiled_patterns = None
    
    @classmethod
    def _get_patterns(cls):
        if cls._compiled_patterns is None:
            cls._compiled_patterns = [
                re.compile(p, re.IGNORECASE) for p in cls.SILENCE_PATTERNS
            ]
        return cls._compiled_patterns
    
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.getMessage())
        
        # Silenciar mensajes muy largos (típicamente JSON-RPC)
        if len(msg) > 500:
            return False
        
        # Silenciar patrones de ruido
        for pattern in self._get_patterns():
            if pattern.search(msg):
                return False
        
        return True


class MCPEventFilter(logging.Filter):
    """
    Transforma mensajes SSE/MCP en logs legibles.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        
        # Detectar y transformar eventos SSE
        if "event: message" in msg or "data:" in msg:
            # Intentar extraer info útil del JSON
            try:
                json_match = re.search(r'\{.*\}', msg, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    record.msg = self._format_mcp_event(data)
                    record.args = ()
            except (json.JSONDecodeError, Exception):
                pass
        
        return True
    
    def _format_mcp_event(self, data: dict) -> str:
        """Formatear evento MCP de forma legible"""
        parts = []
        
        # Determinar tipo de evento
        if "method" in data:
            method = data.get("method", "unknown")
            parts.append(f"📡 {method}")
        elif "result" in data:
            result = data.get("result", {})
            if "tools" in result:
                tools = result.get("tools", [])
                parts.append(f"🔧 Tools disponibles: {len(tools)}")
            else:
                parts.append("✅ Respuesta recibida")
        elif "error" in data:
            error = data.get("error", {})
            parts.append(f"❌ Error: {error.get('message', 'Unknown')}")
        
        return " | ".join(parts) if parts else "📨 Evento MCP"


# ============================================
# Formatter Limpio
# ============================================

class CleanFormatter(logging.Formatter):
    """
    Formatter que produce logs limpios y legibles.
    
    Formato:
        HH:MM:SS.ms LEVEL    [module] mensaje
    
    Con colores por nivel.
    """
    
    LEVEL_COLORS = {
        logging.DEBUG: C.GRAY,
        logging.INFO: C.BLUE,
        logging.WARNING: C.YELLOW,
        logging.ERROR: C.RED,
        logging.CRITICAL: C.RED + C.BOLD,
    }
    
    LEVEL_EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️ ",
        logging.WARNING: "⚠️ ",
        logging.ERROR: "❌",
        logging.CRITICAL: "🔥",
    }
    
    # Mapeo de nombres de módulos a nombres cortos
    MODULE_ALIASES = {
        "sse_starlette.sse": "SSE",
        "uvicorn.access": "HTTP",
        "uvicorn.error": "Server",
        "mcp.server.fastmcp": "MCP",
        "mcp_http_server": "Hub",
        "pretty_logger": "Log",
    }
    
    def __init__(self, use_colors: bool = True, show_module: bool = True):
        super().__init__()
        self.use_colors = use_colors
        self.show_module = show_module
    
    def format(self, record: logging.LogRecord) -> str:
        # Timestamp
        now = datetime.now()
        timestamp = now.strftime("%H:%M:%S") + f".{now.microsecond // 1000:03d}"
        
        # Nivel con color y emoji
        level_color = self.LEVEL_COLORS.get(record.levelno, C.WHITE)
        emoji = self.LEVEL_EMOJIS.get(record.levelno, "📋")
        level_name = record.levelname[:8].ljust(8)
        
        # Módulo (versión corta)
        module = record.name
        for full_name, alias in self.MODULE_ALIASES.items():
            if full_name in module:
                module = alias
                break
        
        # Construir mensaje
        if self.use_colors:
            parts = [
                f"{C.DIM}{timestamp}{C.RESET}",
                f"{level_color}{emoji} {level_name}{C.RESET}",
            ]
            
            if self.show_module and module:
                parts.append(f"{C.DIM}[{module}]{C.RESET}")
            
            parts.append(record.getMessage())
        else:
            parts = [timestamp, level_name]
            if self.show_module and module:
                parts.append(f"[{module}]")
            parts.append(record.getMessage())
        
        return " ".join(parts)


# ============================================
# Handler con Filtrado Inteligente
# ============================================

class SmartStreamHandler(logging.StreamHandler):
    """
    Stream handler que:
    - Aplica filtros automáticamente
    - Usa el formatter limpio
    - Escribe a stderr para no mezclar con stdout
    """
    
    def __init__(self):
        super().__init__(stream=sys.stderr)
        self.setFormatter(CleanFormatter())
        
        # Agregar filtros
        self.addFilter(SSENoiseFilter())
        self.addFilter(MCPEventFilter())


# ============================================
# Configuración Principal
# ============================================

def setup_clean_logging(
    level: int = logging.INFO,
    silence_libraries: Optional[list] = None
) -> logging.Logger:
    """
    Configurar sistema de logging limpio para MCP Hub.
    
    Args:
        level: Nivel mínimo de log (default: INFO)
        silence_libraries: Lista de bibliotecas a silenciar
        
    Returns:
        Logger principal configurado
    """
    # Bibliotecas a silenciar por defecto
    if silence_libraries is None:
        silence_libraries = [
            "sse_starlette.sse",      # Muy ruidoso con pings
            "httpcore",                # Conexiones HTTP
            "httpx",                   # Cliente HTTP
            "asyncio",                 # Loops async
        ]
    
    # Obtener root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Agregar smart handler
    smart_handler = SmartStreamHandler()
    smart_handler.setLevel(level)
    root_logger.addHandler(smart_handler)
    
    # Silenciar bibliotecas ruidosas
    for lib in silence_libraries:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    # Configurar uvicorn para que no logee accesos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return root_logger


def get_clean_log_config() -> dict:
    """
    Obtener configuración de uvicorn para logs limpios.
    
    Uso con uvicorn.run():
        uvicorn.run(app, log_config=get_clean_log_config())
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "clean": {
                "()": CleanFormatter,
            },
        },
        "filters": {
            "sse_noise": {
                "()": SSENoiseFilter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "clean",
                "filters": ["sse_noise"],
                "stream": "ext://sys.stderr",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
            },
            "uvicorn.access": {
                "level": "WARNING",  # Silenciar accesos HTTP
            },
            "sse_starlette.sse": {
                "level": "WARNING",  # Silenciar pings SSE
            },
        },
    }


# ============================================
# Test
# ============================================

if __name__ == "__main__":
    # Demo del logging limpio
    setup_clean_logging(level=logging.DEBUG)
    
    logger = logging.getLogger("TestModule")
    
    print("=" * 60)
    print("Demo: Clean Logging for MCP Hub")
    print("=" * 60)
    
    logger.debug("Este es un mensaje de debug")
    logger.info("Servidor iniciando en puerto 8765")
    logger.warning("Memoria al 85%")
    logger.error("Error de conexión")
    
    # Simular mensaje SSE ruidoso (debería filtrarse)
    sse_logger = logging.getLogger("sse_starlette.sse")
    sse_logger.debug("ping: b': ping - 2026-01-17 03:37:36.481231'")  # NO debería aparecer
    sse_logger.info("Conexión SSE establecida")  # NO debería aparecer (nivel WARNING)
    sse_logger.warning("Cliente desconectado")  # SÍ debería aparecer
    
    print("\n✅ Si solo ves mensajes limpios arriba, el filtrado funciona!")
