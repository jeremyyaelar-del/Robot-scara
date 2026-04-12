#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCARA Robot Trajectory Visualizer
===================================
Recibe datos en tiempo real del Arduino (coordenadas X, Y del efector final),
muestra la trayectoria y el esqueleto del robot en una ventana matplotlib,
y permite exportar la trayectoria capturada a formato DXF.

Protocolo serial esperado de Arduino (una línea por muestra):
    "X:±ddd.dd,Y:±ddd.dd,T1:±ddd.dd,T2:±ddd.dd"
Líneas que empiezan con '#' son comentarios y se ignoran.

Dependencias:
    pip install pyserial matplotlib ezdxf numpy

Uso básico:
    python scara_visualizer.py              # Selecciona puerto en diálogo
    python scara_visualizer.py --port COM3  # Puerto directo (Windows)
    python scara_visualizer.py --port /dev/ttyUSB0 --baud 115200
"""

import argparse
import math
import os
import sys
import threading
import time
from collections import deque
from datetime import datetime
from typing import List, Optional, Tuple

import matplotlib
matplotlib.use("TkAgg")                   # backend compatible con tkinter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, TextBox
import numpy as np

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("[WARN] pyserial no instalado – ejecutando en modo DEMO")

try:
    import ezdxf
    from ezdxf import units as dxf_units
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
    print("[WARN] ezdxf no instalado – exportación DXF desactivada")

# ─── Constantes ───────────────────────────────────────────────────────────
DEFAULT_BAUD    = 115200
DEFAULT_L1      = 150.0   # mm
DEFAULT_L2      = 100.0   # mm
DEFAULT_GR1     = 1.0     # relación de reducción motor 1
DEFAULT_GR2     = 1.0     # relación de reducción motor 2
MAX_TRAIL_PTS   = 10_000  # puntos máximos en buffer de trayectoria
UPDATE_INTERVAL = 30      # ms entre frames de animación

# ══════════════════════════════════════════════════════════════════════════
class ScaraVisualizer:
    """Aplicación principal de visualización y captura de trayectorias."""

    def __init__(self, port: Optional[str], baud: int, l1: float, l2: float,
                 gr1: float = DEFAULT_GR1, gr2: float = DEFAULT_GR2):
        self.port  = port
        self.baud  = baud
        self.L1    = l1
        self.L2    = l2

        # Relaciones de reducción (reductores)
        self.gear_ratio_1 = gr1
        self.gear_ratio_2 = gr2

        # Estado del robot
        self.theta1 = 0.0   # grados
        self.theta2 = 0.0   # grados
        self.x      = l1 + l2
        self.y      = 0.0

        # Trayectoria completa (todos los puntos recibidos)
        self._trail_x: deque = deque(maxlen=MAX_TRAIL_PTS)
        self._trail_y: deque = deque(maxlen=MAX_TRAIL_PTS)

        # Segmento actual de captura activa
        self._capture_x: list = []
        self._capture_y: list = []

        # Historial de segmentos capturados (para DXF)
        self._segments: List[List[Tuple[float, float]]] = []

        # Punto de inicio para trazar líneas rectas (None = espera 1er clic)
        self._line_start: Optional[Tuple[float, float]] = None

        # Lista de líneas rectas trazadas: [(x0,y0), (x1,y1)]
        self._straight_lines: List[Tuple[Tuple[float, float],
                                         Tuple[float, float]]] = []

        # Flags de control
        self._capturing   = False
        self._running     = True
        self._serial_ok   = False

        # Hilo de lectura serial
        self._serial_lock = threading.Lock()
        self._serial: Optional["serial.Serial"] = None

        # Estadísticas
        self._total_points   = 0
        self._captured_count = 0

        self._build_ui()
        self._start_serial()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        """Construye la ventana matplotlib con todos los controles."""
        self.fig = plt.figure(figsize=(13, 8), facecolor="#1e2130")
        self.fig.canvas.manager.set_window_title("SCARA Trajectory Visualizer")

        # Layout: área de plot y panel de controles
        self.ax = self.fig.add_axes([0.05, 0.12, 0.68, 0.82], facecolor="#12141f")
        self._setup_plot_axes()

        # ── Botones ─────────────────────────────────────────────────────
        btn_cfg = dict(color="#2a2d3e", hovercolor="#3a3f5c")

        ax_btn_start  = self.fig.add_axes([0.76, 0.82, 0.21, 0.06])
        ax_btn_stop   = self.fig.add_axes([0.76, 0.74, 0.21, 0.06])
        ax_btn_clear  = self.fig.add_axes([0.76, 0.66, 0.21, 0.06])
        ax_btn_export = self.fig.add_axes([0.76, 0.58, 0.21, 0.06])
        ax_btn_home   = self.fig.add_axes([0.76, 0.50, 0.21, 0.06])
        ax_btn_reset  = self.fig.add_axes([0.76, 0.42, 0.21, 0.06])
        ax_btn_line   = self.fig.add_axes([0.76, 0.34, 0.21, 0.06])

        self.btn_start  = Button(ax_btn_start,  "▶ Iniciar Captura",  **btn_cfg)
        self.btn_stop   = Button(ax_btn_stop,   "■ Detener Captura",  **btn_cfg)
        self.btn_clear  = Button(ax_btn_clear,  "✖ Limpiar",          **btn_cfg)
        self.btn_export = Button(ax_btn_export, "⬇ Exportar DXF",    **btn_cfg)
        self.btn_home   = Button(ax_btn_home,   "⌂ Home",             **btn_cfg)
        self.btn_reset  = Button(ax_btn_reset,  "↺ Reset Contadores", **btn_cfg)
        self.btn_line   = Button(ax_btn_line,   "↗ Línea Recta",      **btn_cfg)

        for btn in (self.btn_start, self.btn_stop, self.btn_clear,
                    self.btn_export, self.btn_home, self.btn_reset,
                    self.btn_line):
            btn.label.set_color("white")
            btn.label.set_fontsize(9)

        self.btn_start .on_clicked(self._on_start)
        self.btn_stop  .on_clicked(self._on_stop)
        self.btn_clear .on_clicked(self._on_clear)
        self.btn_export.on_clicked(self._on_export)
        self.btn_home  .on_clicked(self._on_home)
        self.btn_reset .on_clicked(self._on_reset)
        self.btn_line  .on_clicked(self._on_line_point)

        # ── TextBox para L1, L2, G1, G2 ────────────────────────────────
        ax_l1_lbl = self.fig.add_axes([0.76, 0.27, 0.09, 0.045])
        ax_l1_box = self.fig.add_axes([0.86, 0.27, 0.11, 0.045])
        ax_l2_lbl = self.fig.add_axes([0.76, 0.21, 0.09, 0.045])
        ax_l2_box = self.fig.add_axes([0.86, 0.21, 0.11, 0.045])
        ax_g1_lbl = self.fig.add_axes([0.76, 0.15, 0.09, 0.045])
        ax_g1_box = self.fig.add_axes([0.86, 0.15, 0.11, 0.045])
        ax_g2_lbl = self.fig.add_axes([0.76, 0.09, 0.09, 0.045])
        ax_g2_box = self.fig.add_axes([0.86, 0.09, 0.11, 0.045])

        ax_l1_lbl.set_facecolor("#1e2130"); ax_l1_lbl.axis("off")
        ax_l2_lbl.set_facecolor("#1e2130"); ax_l2_lbl.axis("off")
        ax_g1_lbl.set_facecolor("#1e2130"); ax_g1_lbl.axis("off")
        ax_g2_lbl.set_facecolor("#1e2130"); ax_g2_lbl.axis("off")
        ax_l1_lbl.text(0.5, 0.5, "L1 (mm)", ha="center", va="center",
                       color="white", fontsize=9)
        ax_l2_lbl.text(0.5, 0.5, "L2 (mm)", ha="center", va="center",
                       color="white", fontsize=9)
        ax_g1_lbl.text(0.5, 0.5, "Reducc.1", ha="center", va="center",
                       color="#ffdd88", fontsize=8)
        ax_g2_lbl.text(0.5, 0.5, "Reducc.2", ha="center", va="center",
                       color="#ffdd88", fontsize=8)

        self.tb_l1 = TextBox(ax_l1_box, "", initial=str(self.L1),
                             color="#2a2d3e", hovercolor="#3a3f5c")
        self.tb_l2 = TextBox(ax_l2_box, "", initial=str(self.L2),
                             color="#2a2d3e", hovercolor="#3a3f5c")
        self.tb_g1 = TextBox(ax_g1_box, "", initial=str(self.gear_ratio_1),
                             color="#2a2d3e", hovercolor="#3a3f5c")
        self.tb_g2 = TextBox(ax_g2_box, "", initial=str(self.gear_ratio_2),
                             color="#2a2d3e", hovercolor="#3a3f5c")
        self.tb_l1.label.set_color("white")
        self.tb_l2.label.set_color("white")
        self.tb_g1.label.set_color("#ffdd88")
        self.tb_g2.label.set_color("#ffdd88")
        self.tb_l1.on_submit(self._on_l1_change)
        self.tb_l2.on_submit(self._on_l2_change)
        self.tb_g1.on_submit(self._on_gr1_change)
        self.tb_g2.on_submit(self._on_gr2_change)

        # ── Área de información ─────────────────────────────────────────
        ax_info = self.fig.add_axes([0.76, 0.03, 0.21, 0.05],
                                    facecolor="#12141f")
        ax_info.axis("off")
        self._info_text = ax_info.text(
            0.05, 0.95, self._info_str(),
            ha="left", va="top", color="#aaccff",
            fontsize=8, family="monospace",
            transform=ax_info.transAxes
        )

        # ── Barra de estado ─────────────────────────────────────────────
        ax_status = self.fig.add_axes([0.05, 0.03, 0.68, 0.05],
                                      facecolor="#12141f")
        ax_status.axis("off")
        self._status_text = ax_status.text(
            0.01, 0.5, "Estado: Iniciando...",
            ha="left", va="center", color="#ffdd88",
            fontsize=9, transform=ax_status.transAxes
        )

        self.fig.canvas.mpl_connect("close_event", self._on_close)

    def _setup_plot_axes(self):
        reach = self.L1 + self.L2
        margin = reach * 0.15
        lim = reach + margin
        self.ax.set_xlim(-lim, lim)
        self.ax.set_ylim(-lim, lim)
        self.ax.set_aspect("equal")
        self.ax.set_title("Trayectoria Robot SCARA", color="white", fontsize=11)
        self.ax.set_xlabel("X (mm)", color="#aaaaaa")
        self.ax.set_ylabel("Y (mm)", color="#aaaaaa")
        self.ax.tick_params(colors="#888888")
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#444466")
        self.ax.grid(True, color="#2a2d4a", linewidth=0.5)

        # Círculo de alcance máximo (radio = L1+L2)
        circle = plt.Circle((0, 0), self.L1 + self.L2,
                             color="#3a3f6a", fill=False,
                             linestyle="--", linewidth=0.8)
        self.ax.add_patch(circle)

        # Elementos gráficos dinámicos
        self._line_trail,   = self.ax.plot([], [], "-", color="#00aaff",
                                           linewidth=0.8, alpha=0.6,
                                           label="Trayectoria")
        self._line_capture, = self.ax.plot([], [], "-", color="#00ff88",
                                           linewidth=1.5, alpha=0.9,
                                           label="Captura activa")
        self._line_link1,   = self.ax.plot([], [], "-o", color="#ff8844",
                                           linewidth=2.5, markersize=6,
                                           label="Eslabón 1")
        self._line_link2,   = self.ax.plot([], [], "-o", color="#ffcc44",
                                           linewidth=2.0, markersize=6,
                                           label="Eslabón 2")
        self._dot_ee,       = self.ax.plot([], [], "o", color="#ff4488",
                                           markersize=8, label="Efector final")
        self._dot_origin,   = self.ax.plot([0], [0], "o", color="#ffffff",
                                           markersize=5, label="Base")
        # Líneas rectas trazadas manualmente (segmentos con separador NaN)
        self._line_straight_all, = self.ax.plot([], [], "-", color="#ff44ff",
                                                linewidth=2.0, alpha=0.9,
                                                label="Líneas rectas")
        # Marcador del punto inicial de una línea recta en progreso
        self._dot_line_start, = self.ax.plot([], [], "*", color="#ff44ff",
                                             markersize=12)

        legend = self.ax.legend(loc="upper right", fontsize=7,
                                facecolor="#1e2130", edgecolor="#444466",
                                labelcolor="white")

    # ── Cinemática directa ────────────────────────────────────────────────
    def _forward_kin(self, t1_deg: float, t2_deg: float) -> Tuple[float, float]:
        t1 = math.radians(t1_deg)
        t2 = math.radians(t2_deg)
        x = self.L1 * math.cos(t1) + self.L2 * math.cos(t1 + t2)
        y = self.L1 * math.sin(t1) + self.L2 * math.sin(t1 + t2)
        return x, y

    def _elbow_pos(self, t1_deg: float) -> Tuple[float, float]:
        t1 = math.radians(t1_deg)
        return self.L1 * math.cos(t1), self.L1 * math.sin(t1)

    # ── Lectura serial ────────────────────────────────────────────────────
    def _start_serial(self):
        if not SERIAL_AVAILABLE:
            threading.Thread(target=self._demo_thread, daemon=True).start()
            self._set_status("DEMO – pyserial no disponible")
            return

        port = self.port or self._autodetect_port()
        if port is None:
            self._set_status("ERROR: No se encontró puerto serial")
            threading.Thread(target=self._demo_thread, daemon=True).start()
            return

        try:
            self._serial = serial.Serial(port, self.baud, timeout=1)
            self._serial_ok = True
            self._set_status(f"Conectado → {port} @ {self.baud} baud")
            threading.Thread(target=self._read_thread, daemon=True).start()
        except serial.SerialException as exc:
            self._set_status(f"ERROR al abrir {port}: {exc}")
            threading.Thread(target=self._demo_thread, daemon=True).start()

    def _autodetect_port(self) -> Optional[str]:
        """Busca el primer puerto con un Arduino conocido."""
        for p in serial.tools.list_ports.comports():
            if any(kw in (p.description or "").lower()
                   for kw in ("arduino", "ch340", "cp210", "ftdi", "usb serial")):
                return p.device
        # Fallback: primer puerto disponible
        ports = serial.tools.list_ports.comports()
        return ports[0].device if ports else None

    def _read_thread(self):
        """Hilo dedicado a la lectura serial (no bloquea la UI)."""
        while self._running:
            try:
                raw = self._serial.readline()
                if not raw:
                    continue
                line = raw.decode("ascii", errors="ignore").strip()
                if line.startswith("#") or not line:
                    continue
                self._parse_line(line)
            except Exception:
                pass

    def _demo_thread(self):
        """Genera datos sintéticos para probar la UI sin hardware."""
        t = 0.0
        while self._running:
            t += 0.03
            theta1 = 45.0 * math.sin(t * 0.7)
            theta2 = 30.0 * math.sin(t * 1.3 + 1.0)
            x, y = self._forward_kin(theta1, theta2)
            with self._serial_lock:
                self.theta1 = theta1
                self.theta2 = theta2
                self.x = x
                self.y = y
                self._trail_x.append(x)
                self._trail_y.append(y)
                self._total_points += 1
                if self._capturing:
                    self._capture_x.append(x)
                    self._capture_y.append(y)
                    self._captured_count += 1
            time.sleep(0.02)

    def _parse_line(self, line: str):
        """Analiza una línea del formato 'X:v,Y:v,T1:v,T2:v'."""
        try:
            parts = {p.split(":")[0]: float(p.split(":")[1])
                     for p in line.split(",") if ":" in p}
            x  = parts.get("X", self.x)
            y  = parts.get("Y", self.y)
            t1 = parts.get("T1", self.theta1)
            t2 = parts.get("T2", self.theta2)
        except (ValueError, IndexError):
            return

        with self._serial_lock:
            self.x = x
            self.y = y
            self.theta1 = t1
            self.theta2 = t2
            self._trail_x.append(x)
            self._trail_y.append(y)
            self._total_points += 1
            if self._capturing:
                self._capture_x.append(x)
                self._capture_y.append(y)
                self._captured_count += 1

    # ── Animación ─────────────────────────────────────────────────────────
    def _animate(self, _frame):
        with self._serial_lock:
            tx = list(self._trail_x)
            ty = list(self._trail_y)
            cx = list(self._capture_x)
            cy = list(self._capture_y)
            x, y = self.x, self.y
            t1, t2 = self.theta1, self.theta2
            sl = list(self._straight_lines)
            ls = self._line_start

        # Trayectoria completa
        self._line_trail.set_data(tx, ty)

        # Captura activa
        self._line_capture.set_data(cx, cy)

        # Esqueleto del robot
        ex, ey = self._elbow_pos(t1)
        self._line_link1.set_data([0, ex], [0, ey])
        self._line_link2.set_data([ex, x], [ey, y])
        self._dot_ee.set_data([x], [y])

        # Líneas rectas trazadas (usando NaN como separador de segmentos)
        if sl:
            nan = float("nan")
            xs, ys = [], []
            for (x0, y0), (x1, y1) in sl:
                xs += [x0, x1, nan]
                ys += [y0, y1, nan]
            self._line_straight_all.set_data(xs, ys)
        else:
            self._line_straight_all.set_data([], [])

        # Marcador del punto inicial en espera del segundo clic
        if ls is not None:
            self._dot_line_start.set_data([ls[0]], [ls[1]])
        else:
            self._dot_line_start.set_data([], [])

        # Panel informativo
        self._info_text.set_text(self._info_str(x, y, t1, t2))

        return (self._line_trail, self._line_capture,
                self._line_link1, self._line_link2,
                self._dot_ee, self._line_straight_all,
                self._dot_line_start, self._info_text)

    def _info_str(self, x=None, y=None, t1=None, t2=None) -> str:
        x  = x  if x  is not None else self.x
        y  = y  if y  is not None else self.y
        t1 = t1 if t1 is not None else self.theta1
        t2 = t2 if t2 is not None else self.theta2

        # Longitud de la trayectoria capturada
        trail_len = 0.0
        with self._serial_lock:
            cx = list(self._capture_x)
            cy = list(self._capture_y)
        for i in range(1, len(cx)):
            trail_len += math.hypot(cx[i] - cx[i-1], cy[i] - cy[i-1])

        return (
            f"X:{x:+7.1f}mm  Y:{y:+7.1f}mm\n"
            f"θ1:{t1:+7.1f}°  θ2:{t2:+7.1f}°\n"
            f"Pts:{self._total_points:<5d} Seg:{len(self._segments)}\n"
        )

    def _set_status(self, msg: str):
        try:
            self._status_text.set_text(f"Estado: {msg}")
        except Exception:
            pass

    # ── Callbacks de botones ──────────────────────────────────────────────
    def _on_start(self, _event):
        with self._serial_lock:
            if not self._capturing:
                self._capturing = True
                self._capture_x = []
                self._capture_y = []
                self._captured_count = 0
        self._set_status("● Capturando trayectoria...")
        self._line_capture.set_color("#00ff88")

    def _on_stop(self, _event):
        with self._serial_lock:
            if self._capturing:
                self._capturing = False
                seg = list(zip(self._capture_x, self._capture_y))
                if len(seg) >= 2:
                    self._segments.append(seg)
        self._set_status(f"■ Captura detenida – {len(self._segments)} segmento(s) guardado(s)")

    def _on_clear(self, _event):
        with self._serial_lock:
            self._capturing = False
            self._trail_x.clear()
            self._trail_y.clear()
            self._capture_x = []
            self._capture_y = []
            self._segments  = []
            self._total_points   = 0
            self._captured_count = 0
            self._straight_lines = []
        self._line_start = None
        self._set_status("Trayectoria limpiada")

    def _on_export(self, _event):
        if not EZDXF_AVAILABLE:
            self._set_status("ERROR: ezdxf no instalado – no se puede exportar")
            return

        with self._serial_lock:
            segments = [list(s) for s in self._segments]
            straight = list(self._straight_lines)
            # También incluir captura activa si tiene puntos
            if self._capture_x and len(self._capture_x) >= 2:
                segments.append(list(zip(self._capture_x, self._capture_y)))

        if not segments and not straight:
            self._set_status("Sin trayectoria capturada para exportar")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scara_trajectory_{ts}.dxf"
        try:
            self._export_dxf(segments, straight, filename)
            self._set_status(f"DXF exportado → {filename}")
        except Exception as exc:
            self._set_status(f"ERROR exportando DXF: {exc}")

    def _on_home(self, _event):
        if self._serial and self._serial_ok:
            try:
                self._serial.write(b"H\n")
                self._set_status("Comando HOME enviado al Arduino")
            except Exception as exc:
                self._set_status(f"ERROR enviando HOME: {exc}")
        else:
            self._set_status("No hay conexión serial activa")

    def _on_reset(self, _event):
        if self._serial and self._serial_ok:
            try:
                self._serial.write(b"R\n")
                self._set_status("Comando RESET enviado al Arduino")
            except Exception as exc:
                self._set_status(f"ERROR enviando RESET: {exc}")
        else:
            self._set_status("No hay conexión serial activa")

    def _on_line_point(self, _event):
        """Traza una línea recta entre dos posiciones del efector final.

        Primer clic  → marca el punto de inicio (estrella magenta en el plot).
        Segundo clic → dibuja la línea recta hasta la posición actual y la
                       guarda como segmento exportable.
        """
        with self._serial_lock:
            x, y = self.x, self.y

        if self._line_start is None:
            # ── Primer clic: guardar punto de inicio ──────────────────
            self._line_start = (x, y)
            self._set_status(
                f"✦ Punto inicial marcado ({x:.1f}, {y:.1f}) "
                "– presiona de nuevo para trazar la línea"
            )
        else:
            # ── Segundo clic: crear la línea recta ────────────────────
            start = self._line_start
            self._line_start = None
            with self._serial_lock:
                self._straight_lines.append((start, (x, y)))
                # Registrar como segmento de dos puntos para exportación DXF
                self._segments.append([start, (x, y)])
            self._set_status(
                f"↗ Línea recta: ({start[0]:.1f},{start[1]:.1f}) → "
                f"({x:.1f},{y:.1f})"
            )

    def _on_l1_change(self, text: str):
        try:
            val = float(text)
            if val > 0:
                self.L1 = val
                if self._serial and self._serial_ok:
                    self._serial.write(f"L1:{val:.1f}\n".encode())
                self._set_status(f"L1 actualizado → {val:.1f} mm")
                self._refresh_reach_circle()
        except ValueError:
            self._set_status("ERROR: L1 debe ser un número positivo")

    def _on_l2_change(self, text: str):
        try:
            val = float(text)
            if val > 0:
                self.L2 = val
                if self._serial and self._serial_ok:
                    self._serial.write(f"L2:{val:.1f}\n".encode())
                self._set_status(f"L2 actualizado → {val:.1f} mm")
                self._refresh_reach_circle()
        except ValueError:
            self._set_status("ERROR: L2 debe ser un número positivo")

    def _on_gr1_change(self, text: str):
        try:
            val = float(text)
            if val > 0:
                self.gear_ratio_1 = val
                if self._serial and self._serial_ok:
                    self._serial.write(f"G1:{val:.3f}\n".encode())
                self._set_status(f"Reducción motor 1 → {val:.3f}")
            else:
                self._set_status("ERROR: Reducc.1 debe ser > 0")
        except ValueError:
            self._set_status("ERROR: Reducc.1 debe ser un número positivo")

    def _on_gr2_change(self, text: str):
        try:
            val = float(text)
            if val > 0:
                self.gear_ratio_2 = val
                if self._serial and self._serial_ok:
                    self._serial.write(f"G2:{val:.3f}\n".encode())
                self._set_status(f"Reducción motor 2 → {val:.3f}")
            else:
                self._set_status("ERROR: Reducc.2 debe ser > 0")
        except ValueError:
            self._set_status("ERROR: Reducc.2 debe ser un número positivo")

    def _refresh_reach_circle(self):
        """Actualiza el círculo de alcance máximo al cambiar L1/L2."""
        for patch in self.ax.patches[:]:
            patch.remove()
        reach = self.L1 + self.L2
        circle = plt.Circle((0, 0), reach,
                             color="#3a3f6a", fill=False,
                             linestyle="--", linewidth=0.8)
        self.ax.add_patch(circle)
        margin = reach * 0.15
        lim = reach + margin
        self.ax.set_xlim(-lim, lim)
        self.ax.set_ylim(-lim, lim)

    def _on_close(self, _event):
        self._running = False
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass

    # ── Exportación DXF ───────────────────────────────────────────────────
    def _export_dxf(self, segments: list, straight_lines: list, filename: str):
        """Genera un archivo DXF con las trayectorias capturadas."""
        doc = ezdxf.new(dxfversion="R2010")
        doc.units = dxf_units.MM

        # Capas
        doc.layers.new(name="TRAJECTORY",
                       dxfattribs={"color": 1, "linetype": "CONTINUOUS"})
        doc.layers.new(name="STRAIGHT_LINES",
                       dxfattribs={"color": 6, "linetype": "CONTINUOUS"})
        doc.layers.new(name="METADATA",
                       dxfattribs={"color": 7, "linetype": "CONTINUOUS"})

        msp = doc.modelspace()

        for idx, seg in enumerate(segments, start=1):
            if len(seg) < 2:
                continue
            # Convertir a lista de tuplas (x, y)
            pts = [(float(p[0]), float(p[1])) for p in seg]
            # Polilínea lightweight (lwpolyline) en el plano XY
            msp.add_lwpolyline(pts, close=False,
                               dxfattribs={"layer": "TRAJECTORY",
                                           "color": idx % 7 + 1})

        for (x0, y0), (x1, y1) in straight_lines:
            msp.add_line((float(x0), float(y0)), (float(x1), float(y1)),
                         dxfattribs={"layer": "STRAIGHT_LINES", "color": 6})

        # Texto de metadatos
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = (
            f"Generado: {ts}  |  "
            f"L1={self.L1:.1f}mm  L2={self.L2:.1f}mm  |  "
            f"Segmentos={len(segments)}  Líneas rectas={len(straight_lines)}"
        )
        total_pts = sum(len(s) for s in segments)
        msp.add_text(
            metadata,
            dxfattribs={
                "layer": "METADATA",
                "height": 2.0,
                "insert": (0, -(self.L1 + self.L2) * 1.2),
                "color": 7,
            }
        )

        doc.saveas(filename)

    # ── Arranque ──────────────────────────────────────────────────────────
    def run(self):
        self._anim = FuncAnimation(
            self.fig, self._animate,
            interval=UPDATE_INTERVAL,
            blit=True,
            cache_frame_data=False
        )
        plt.tight_layout(pad=1.0)
        plt.show()


# ══════════════════════════════════════════════════════════════════════════
def _list_ports():
    """Imprime los puertos seriales disponibles."""
    if not SERIAL_AVAILABLE:
        print("pyserial no instalado")
        return
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No se encontraron puertos seriales")
        return
    print("Puertos seriales disponibles:")
    for p in ports:
        print(f"  {p.device:15s}  {p.description}")


def main():
    parser = argparse.ArgumentParser(
        description="SCARA Robot Trajectory Visualizer"
    )
    parser.add_argument("--port", default=None,
                        help="Puerto serial (ej: COM3, /dev/ttyUSB0). "
                             "Si se omite, se autodetecta o se usa modo DEMO.")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD,
                        help=f"Velocidad serial (default: {DEFAULT_BAUD})")
    parser.add_argument("--l1", type=float, default=DEFAULT_L1,
                        help=f"Longitud eslabón 1 en mm (default: {DEFAULT_L1})")
    parser.add_argument("--l2", type=float, default=DEFAULT_L2,
                        help=f"Longitud eslabón 2 en mm (default: {DEFAULT_L2})")
    parser.add_argument("--gr1", type=float, default=DEFAULT_GR1,
                        help=f"Relación de reducción motor 1 (default: {DEFAULT_GR1})")
    parser.add_argument("--gr2", type=float, default=DEFAULT_GR2,
                        help=f"Relación de reducción motor 2 (default: {DEFAULT_GR2})")
    parser.add_argument("--list-ports", action="store_true",
                        help="Listar puertos seriales disponibles y salir")
    args = parser.parse_args()

    if args.list_ports:
        _list_ports()
        sys.exit(0)

    app = ScaraVisualizer(
        port=args.port,
        baud=args.baud,
        l1=args.l1,
        l2=args.l2,
        gr1=args.gr1,
        gr2=args.gr2,
    )
    app.run()


if __name__ == "__main__":
    main()
