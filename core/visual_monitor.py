"""
Visual Activity Monitor - Para hacer la interfaz MCP más dinámica e interactiva
"""

import asyncio
import threading
import time
import random
from datetime import datetime
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path

try:
    from pretty_logger import get_logger, Colors
    logger = get_logger("Visual-Monitor")
except ImportError:
    logger = None
    Colors = None

class VisualActivityMonitor:
    """
    Monitor de actividad visual que muestra:
    - Actividad de herramientas en tiempo real
    - Estadísticas dinámicas
    - Efectos visuales interactivos
    """
    
    def __init__(self):
        self.active_tools: List[Dict[str, Any]] = []
        self.completed_tools: List[Dict[str, Any]] = []
        self.error_tools: List[Dict[str, Any]] = []
        self.tool_counter = 0
        self.total_tools_executed = 0
        self.total_available_tools = 31
        self.start_time = datetime.now()
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.v9_sequence = 0
        self.vortex_sequence = 0
        self.stats_sequence = 0
        self.last_activity_time = time.time()
        self.random_effect_counter = 0
        
    def start_monitoring(self):
        """Iniciar el monitoreo visual"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        if logger:
            logger.info("Visual Activity Monitor iniciado")
        else:
            print("MONITOR: Visual Activity Monitor STARTED")
    
    def stop_monitoring(self):
        """Detener el monitoreo visual"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        if logger:
            logger.info("Visual Activity Monitor detenido")
        else:
            print("MONITOR: Visual Activity Monitor STOPPED")
    
    def _monitor_loop(self):
        """Bucle principal de monitoreo"""
        while self.monitoring:
            try:
                self.v9_sequence += 1
                self.vortex_sequence += 1
                self.stats_sequence += 1
                
                # Mostrar diferentes efectos visuales
                if self.v9_sequence % 3 == 0:
                    self._show_v9_pulse()
                
                if self.vortex_sequence % 5 == 0:
                    self._show_vortex_heartbeat()
                
                if self.stats_sequence % 7 == 0:
                    self._update_v9_stats()
                
                if self.random_effect_counter % 10 == 0:
                    self._show_random_effect()
                
                self.random_effect_counter += 1
                
                time.sleep(0.1)  # Actualización rápida para efectos fluidos
                
            except Exception as e:
                if logger:
                    logger.error(f"Error en monitor loop: {e}")
                else:
                    print(f"MONITOR ERROR: {e}")
                time.sleep(1)
    
    def tool_started(self, tool_name: str, args: Dict[str, Any]):
        """Notificar inicio de herramienta"""
        self.tool_counter += 1
        tool_info = {
            'id': self.tool_counter,
            'name': tool_name,
            'start_time': time.time(),
            'args': args,
            'status': 'running'
        }
        self.active_tools.append(tool_info)
        self.last_activity_time = time.time()
        self._show_tool_start(tool_info)
    
    def tool_completed(self, tool_name: str, result: Any, duration: float = 0.0):
        """Notificar completación de herramienta"""
        self.total_tools_executed += 1
        
        # Encontrar y mover de active a completed
        for i, tool in enumerate(self.active_tools):
            if tool['name'] == tool_name and tool['status'] == 'running':
                tool['end_time'] = time.time()
                tool['duration'] = duration
                tool['result'] = result
                tool['status'] = 'completed'
                self.completed_tools.append(tool)
                self.active_tools.pop(i)
                self._show_tool_complete(tool)
                break
    
    def tool_error(self, tool_name: str, error: str, duration: float = 0.0):
        """Notificar error de herramienta"""
        self.total_tools_executed += 1
        
        # Encontrar y mover de active a error
        for i, tool in enumerate(self.active_tools):
            if tool['name'] == tool_name and tool['status'] == 'running':
                tool['end_time'] = time.time()
                tool['duration'] = duration
                tool['error'] = error
                tool['status'] = 'error'
                self.error_tools.append(tool)
                self.active_tools.pop(i)
                self._show_tool_error(tool)
                break
    
    def _show_v9_pulse(self):
        """Mostrar pulso V9 con efectos Matrix"""
        if not logger and not Colors:
            return
            
        sequence = f"{self.v9_sequence:04d}"
        active_count = len(self.active_tools)
        
        # Generar nombres de herramientas en formato Matrix
        if self.active_tools:
            names_display = " ".join([tool['name'][:6] for tool in self.active_tools[:5]])
            if len(self.active_tools) > 5:
                names_display += f" +{len(self.active_tools)-5}"
        else:
            names_display = "SYSTEM_IDLE"
        
        if logger and Colors:
            # Versión con colores
            colored_names = f"{Colors.GREEN_MINT}{names_display}{Colors.RESET}"
            bit_stream = "".join([random.choice(["0", "1"]) for _ in range(16)])
            colored_bits = f"{Colors.GREEN}{bit_stream}{Colors.RESET}"
            
            logger.info(f"  {colored_names} [{colored_bits}] SEQ:{sequence}")
            
            # Mostrar actividad de herramientas si hay suficientes activas
            if active_count > 3:
                tools_matrix = [tool['name'][:4] for tool in self.active_tools[:8]]
                tools_stream = " ".join(tools_matrix)
                logger.info(f"  Matrix Stream: {tools_stream}")
        else:
            # Fallback sin colores
            print(f"  {names_display} [{''.join([random.choice(['0', '1']) for _ in range(16)])}] SEQ:{sequence}")
            
            if active_count > 3:
                tools_matrix = [tool['name'][:4] for tool in self.active_tools[:8]]
                tools_stream = " ".join(tools_matrix)
                print(f"  Matrix Stream: {tools_stream}")
    
    def _show_vortex_heartbeat(self):
        """Mostrar latido del Vortex con estilo Matrix"""
        if not logger and not Colors:
            return
            
        heartbeat_seq = f"{self.vortex_sequence:04d}"
        
        if logger and Colors:
            logger.info(f"  {Colors.GREEN_MINT}Context Vortex{Colors.RESET} [{Colors.GREEN}ACTIVE{Colors.RESET}] PULSE:{heartbeat_seq}")
            
            # Generar líneas Matrix para el vórtice
            for i in range(3):
                line = "".join([random.choice(["0", "1", " ", "·"]) for _ in range(32)])
                colored_line = f"{Colors.GREEN_MINT}{line}{Colors.RESET}"
                logger.info(f"  {colored_line}")
        else:
            print(f"  Context Vortex [ACTIVE] PULSE:{heartbeat_seq}")
            
            for i in range(3):
                line = "".join([random.choice(["0", "1", " ", "·"]) for _ in range(32)])
                print(f"  {line}")
    
    def _show_v9_effects(self):
        """Mostrar efectos V9 adicionales"""
        if not logger and not Colors:
            return
            
        seq_num = f"{self.v9_sequence:04d}"
        
        # Efecto Matrix Rain
        if random.random() < 0.3:
            rain_line = "".join([random.choice(["0", "1", " ", "·", "•"]) for _ in range(24)])
            if logger and Colors:
                logger.info(f"  {Colors.GREEN_MINT}RAIN{Colors.RESET} [{Colors.GREEN}{rain_line}{Colors.RESET}] SEQ:{seq_num}")
            else:
                print(f"  RAIN [{rain_line}] SEQ:{seq_num}")
        
        # Efecto Binary Stream
        if random.random() < 0.2:
            binary_stream = "".join([random.choice(["0", "1"]) for _ in range(16)])
            if logger and Colors:
                logger.info(f"  {Colors.GREEN_MINT}BINARY{Colors.RESET} [{Colors.GREEN}{binary_stream}{Colors.RESET}] STREAM")
            else:
                print(f"  BINARY [{binary_stream}] STREAM")
        
        # Efecto Data Corruption
        if random.random() < 0.1:
            corrupt_data = "".join([random.choice(["X", "#", "!", "?", "%"]) for _ in range(8)])
            if logger and Colors:
                logger.warning(f"  {Colors.YELLOW}CORRUPT{Colors.RESET} [{Colors.RED}{corrupt_data}{Colors.RESET}] DETECTED")
            else:
                print(f"  CORRUPT [{corrupt_data}] DETECTED")
        
        # Efecto System Pulse
        if random.random() < 0.4:
            pulse_pattern = "".join([random.choice(["█", "▓", "▒", "░", " "]) for _ in range(12)])
            if logger and Colors:
                logger.info(f"  {Colors.CYAN}PULSE{Colors.RESET} [{Colors.GREEN_MINT}{pulse_pattern}{Colors.RESET}] SYSTEM")
            else:
                print(f"  PULSE [{pulse_pattern}] SYSTEM")
    
    def _show_tool_start(self, tool_info: Dict[str, Any]):
        """Mostrar inicio de herramienta con estilo"""
        if not logger and not Colors:
            return
            
        tool_name = tool_info['name']
        tool_id = tool_info['id']
        
        # Generar patrón Matrix para la herramienta
        activation_pattern = "".join([random.choice(["0", "1"]) for _ in range(8)])
        
        if logger and Colors:
            logger.info(f"  {Colors.GREEN}▶{Colors.RESET} {Colors.CYAN}{tool_name}{Colors.RESET} [{Colors.GREEN_MINT}{activation_pattern}{Colors.RESET}] ID:{tool_id}")
            
            # Mostrar patrón de activación
            status_bits = "".join([random.choice(["0", "1"]) for _ in range(12)])
            logger.info(f"  {Colors.GREEN_MINT}ACTIVATION{Colors.RESET} [{Colors.GREEN}{status_bits}{Colors.RESET}] STATUS:RUNNING")
        else:
            print(f"  ▶ {tool_name} [{activation_pattern}] ID:{tool_id}")
            status_bits = "".join([random.choice(["0", "1"]) for _ in range(12)])
            print(f"  ACTIVATION [{status_bits}] STATUS:RUNNING")
        
        # Actualizar contador visual
        active_count = len(self.active_tools)
        active_bits = "".join(["1" for _ in range(min(active_count, 12))] + ["0" for _ in range(max(0, 12-active_count))])
        
        if logger and Colors:
            logger.info(f"  {Colors.GREEN_MINT}Active Tools{Colors.RESET} [{Colors.GREEN}{active_bits}{Colors.RESET}] ({active_count:2d}/30)")
        else:
            print(f"  Active Tools [{active_bits}] ({active_count:2d}/30)")
    
    def _show_tool_complete(self, tool_info: Dict[str, Any]):
        """Mostrar completación de herramienta"""
        if not logger and not Colors:
            return
            
        tool_name = tool_info['name']
        duration = tool_info.get('duration', 0.0)
        
        # Patrón de éxito
        success_pattern = "".join([random.choice(["1", "✓"]) for _ in range(8)])
        
        if logger and Colors:
            logger.info(f"  {Colors.GREEN}✓{Colors.RESET} {Colors.CYAN}{tool_name}{Colors.RESET} [{Colors.GREEN_MINT}{success_pattern}{Colors.RESET}] {duration:.2f}s")
            
            # Bits de éxito
            success_bits = "".join(["1" for _ in range(min(8, int(duration*2)))])
            logger.info(f"  {Colors.GREEN_MINT}SUCCESS{Colors.RESET} [{Colors.GREEN}{success_bits}{Colors.RESET}] COMPLETED")
        else:
            print(f"  ✓ {tool_name} [{success_pattern}] {duration:.2f}s")
            success_bits = "".join(["1" for _ in range(min(8, int(duration*2)))])
            print(f"  SUCCESS [{success_bits}] COMPLETED")
        
        # Herramientas restantes activas
        remaining_count = len(self.active_tools)
        remaining_bits = "".join(["1" for _ in range(min(remaining_count, 8))] + ["0" for _ in range(max(0, 8-remaining_count))])
        
        if logger and Colors:
            logger.info(f"  {Colors.GREEN_MINT}Remaining Active{Colors.RESET} [{Colors.CYAN}{remaining_bits}{Colors.RESET}] ({remaining_count:2d}/30)")
        else:
            print(f"  Remaining Active [{remaining_bits}] ({remaining_count:2d}/30)")
    
    def _show_tool_error(self, tool_info: Dict[str, Any]):
        """Mostrar error de herramienta"""
        if not logger and not Colors:
            return
            
        tool_name = tool_info['name']
        error_msg = tool_info.get('error', 'Unknown error')
        
        # Patrón de error
        error_pattern = "".join([random.choice(["0", "X", "!"]) for _ in range(8)])
        
        if logger and Colors:
            logger.error(f"  {Colors.RED}✗{Colors.RESET} {Colors.CYAN}{tool_name}{Colors.RESET} [{Colors.RED}{error_pattern}{Colors.RESET}] ERROR")
            logger.error(f"  {Colors.RED}MESSAGE{Colors.RESET}: {error_msg[:40]}...")
        else:
            print(f"  ✗ {tool_name} [{error_pattern}] ERROR")
            print(f"  MESSAGE: {error_msg[:40]}...")
        
        # Datos corruptos
        corrupt_data = "".join([random.choice(["X", "#", "!", "?", "%%"]) for _ in range(12)])
        
        if logger and Colors:
            logger.warning(f"  {Colors.YELLOW}Corrupt Stream{Colors.RESET} [{Colors.RED}{corrupt_data}{Colors.RESET}] DETECTED")
        else:
            print(f"  Corrupt Stream [{corrupt_data}] DETECTED")
    
    def _show_active_status(self):
        """Mostrar estado de herramientas activas"""
        if not logger or not Colors:
            return
            
        if not self.active_tools:
            return
        
        # Crear barra de actividad
        active_count = len(self.active_tools)
        activity_level = min(1.0, active_count / 10.0)
        activity_bar = "█" * int(activity_level * 20)
        
        # Nombres de herramientas activas
        tools_names = [tool['name'][:8] for tool in self.active_tools[:5]]  # Primeras 5 herramientas
        if len(self.active_tools) > 5:
            tools_names.append(f"+{len(self.active_tools)-5}more")
        
        # Colorear según nivel de actividad
        if activity_level > 0.8:
            color = Colors.RED
        elif activity_level > 0.5:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN
        
        status_line = f"{Colors.GREEN_MINT}🔥 ACTIVITY: {active_count:2d}/{visual_monitor.total_available_tools} tools [{activity_bar:20}] {', '.join(tools_names)}{Colors.RESET}"
        print(f"\n{status_line}", file=sys.stderr)
    
    def _update_v9_stats(self):
        """Actualizar estadísticas con representación Matrix"""
        if not logger and not Colors:
            return
            
        seq_num = f"{self.stats_sequence:04d}"
        active_count = len(self.active_tools)
        
        # Estadísticas en formato Matrix
        total_tools_available = self.total_available_tools
        total_tools_executed = self.total_tools_executed
        
        # Representación binaria
        total_bits = bin(total_tools_available)[2:].zfill(8)
        active_bits = bin(active_count)[2:].zfill(8)
        
        if logger and Colors:
            logger.info(f"  {Colors.CYAN}STATS{Colors.RESET} {Colors.GREEN_MINT}{seq_num}{Colors.RESET} Matrix System Analytics")
            logger.info(f"  Available: {Colors.GREEN}{total_tools_available}{Colors.RESET} [{Colors.GREEN_MINT}{total_bits}{Colors.RESET}] | Active: {Colors.YELLOW}{active_count}{Colors.RESET} [{Colors.GREEN_MINT}{active_bits}{Colors.RESET}] | Executed: {Colors.CYAN}{total_tools_executed}{Colors.RESET}")
        else:
            print(f"  STATS {seq_num} Matrix System Analytics")
            print(f"  Available: {total_tools_available} [{total_bits}] | Active: {active_count} [{active_bits}] | Executed: {total_tools_executed}")
        
        # Checksum Matrix
        checksum = (total_tools_available + active_count + total_tools_executed) % 65536
        checksum_hex = f"{checksum:04X}"
        checksum_binary = bin(checksum)[2:].zfill(16)
        
        if logger and Colors:
            logger.info(f"  Checksum: {Colors.GREEN}0x{checksum_hex}{Colors.RESET} [{Colors.GREEN_MINT}{checksum_binary}{Colors.RESET}] | Pattern: {active_bits[:8]}")
        else:
            print(f"  Checksum: 0x{checksum_hex} [{checksum_binary}] | Pattern: {active_bits[:8]}")
        
        # Stream de actividad reciente
        recent_tools = self.completed_tools[-5:]  # Últimas 5 herramientas
        if recent_tools:
            recent_stream = " ".join([tool['name'][:4] for tool in recent_tools])
            if logger and Colors:
                logger.info(f"  Recent Activity: [{Colors.CYAN}{recent_stream}{Colors.RESET}]")
            else:
                print(f"  Recent Activity: [{recent_stream}]")
    
    def _show_random_effect(self):
        """Mostrar efecto visual aleatorio"""
        if not logger or not Colors:
            return
            
        effect_type = random.choice(["RAIN", "BINARY", "BYTES", "PATTERN"])
        seq_num = f"{self.random_effect_counter:04d}"
        
        if effect_type == "RAIN":
            rain_line = "".join([random.choice(["0", "1", " ", "·", "•"]) for _ in range(32)])
            print(f"\n{Colors.GREEN_MINT}RAIN{Colors.RESET} [{Colors.GREEN}{rain_line}{Colors.RESET}] SEQ:{seq_num}", file=sys.stderr)
        
        elif effect_type == "BINARY":
            binary_line = "".join([random.choice(["0", "1"]) for _ in range(24)])
            print(f"\n{Colors.GREEN_MINT}BINARY{Colors.RESET} [{Colors.GREEN}{binary_line}{Colors.RESET}] STREAM", file=sys.stderr)
        
        elif effect_type == "BYTES":
            hex_line = "".join([f"{random.randint(0,255):02X}" for _ in range(8)])
            print(f"\n{Colors.GREEN_MINT}BYTES{Colors.RESET} [{Colors.CYAN}{hex_line}{Colors.RESET}] DATA", file=sys.stderr)
        
        elif effect_type == "PATTERN":
            pattern_line = "".join([random.choice(["█", "▓", "▒", "░", " "]) for _ in range(16)])
            print(f"\n{Colors.GREEN_MINT}PATTERN{Colors.RESET} [{Colors.CYAN}{pattern_line}{Colors.RESET}] MATRIX", file=sys.stderr)
    
    def show_matrix_rain(self):
        """Mostrar lluvia Matrix clásica"""
        if not logger or not Colors:
            return
            
        rain_chars = ["0", "1", " ", "·", "•", "█", "▓", "▒", "░"]
        rain_line = "".join([random.choice(rain_chars) for _ in range(40)])
        brightness = Colors.GREEN_MINT if random.random() > 0.5 else Colors.GREEN
        print(f"\n{brightness}{rain_line}{Colors.RESET}", file=sys.stderr)
    
    def show_tool_activity_bar(self):
        """Mostrar barra de actividad de herramientas"""
        if not logger or not Colors:
            return
            
        active_count = len(self.active_tools)
        activity_level = min(1.0, active_count / 10.0)
        activity_bar = "█" * int(activity_level * 20)
        
        # Colorear según nivel de actividad
        if activity_level > 0.8:
            color = Colors.RED
        elif activity_level > 0.5:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN
        
        # Nombres de herramientas activas
        tools_names = [tool['name'][:8] for tool in self.active_tools[:5]]  # Primeras 5 herramientas
        if len(self.active_tools) > 5:
            tools_names.append(f"+{len(self.active_tools)-5}more")
        
        print(f"\n{Colors.GREEN_MINT}🔥 ACTIVITY: {active_count:2d}/{visual_monitor.total_available_tools} tools [{activity_bar:20}] {', '.join(tools_names)}{Colors.RESET}", file=sys.stderr)
    
    def show_activity_matrix(self):
        """Mostrar matriz de actividad"""
        if not logger or not Colors:
            return
            
        # Generar línea Matrix para actividad
        matrix_chars = ["0", "1", " ", "·", "•"]
        matrix_line = "".join([random.choice(matrix_chars) for _ in range(36)])
        
        # Agregar información de actividad
        active_count = len(self.active_tools)
        completed_count = len(self.completed_tools)
        error_count = len(self.error_tools)
        
        activity_info = f"A:{active_count} C:{completed_count} E:{error_count}"
        
        color = Colors.GREEN_MINT if active_count > 0 else Colors.CYAN
        print(f"\n{color}{matrix_line} {activity_info}{Colors.RESET}", file=sys.stderr)

def get_visual_monitor() -> VisualActivityMonitor:
    """Obtener el monitor visual global"""
    return visual_monitor

# Instancia global del monitor
visual_monitor = VisualActivityMonitor()

if __name__ == "__main__":
    print("""
Visual Activity Monitor - Para hacer la interfaz MCP más dinámica e interactiva
    """)
    import argparse
    
    parser = argparse.ArgumentParser(description="Visual Activity Monitor - Matrix Style")
    parser.add_argument("--verbose", "-v", action="store_true", help="Activar modo verbose")
    parser.add_argument("--demo", "-d", action="store_true", help="Ejecutar demo de Matrix")
    
    args = parser.parse_args()
    
    if args.demo:
        print("🎬 Iniciando demo Matrix...")
        monitor = get_visual_monitor()
        monitor.start_monitoring()
        
        # Simular actividad Matrix
        tool_names = ["search", "read", "write", "grep", "glob", "skill", "web", "todo", "command", "diagnostics"]
        
        for i in range(20):
            tool = random.choice(tool_names)
            monitor.tool_started(tool, {"test": i})
            
            if random.random() < 0.7:
                time.sleep(random.uniform(0.5, 2.0))
                monitor.tool_completed(tool, f"result_{i}", random.uniform(0.1, 1.5))
            else:
                time.sleep(random.uniform(0.1, 0.5))
        
        time.sleep(3)
        monitor.stop_monitoring()
        print("✅ Demo Matrix completada")
    
    else:
        print("👁️  Monitor Visual Matrix iniciado")
        print("Use --demo para ver una demostración")
        print("Use --verbose para modo detallado")
        
        monitor = get_visual_monitor()
        monitor.start_monitoring()
        
        try:
            print("🔄 Monitor ejecutándose... Presione Ctrl+C para salir")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo monitor...")
            monitor.stop_monitoring()
            print("✅ Monitor detenido")