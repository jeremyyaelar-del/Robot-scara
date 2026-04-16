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
DEFAULT_STAMP_RADIUS_MM = 5.0   # radio por defecto del círculo timbrado (mm) → diámetro 1 cm
SNAP_RADIUS         = 15.0  # mm – distancia de snap para la herramienta de polilínea
COLLINEARITY_EPSILON = 1e-9  # umbral para detectar puntos colineales

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

        # Eje Z (controlado independientemente; no hay encoder, se sigue localmente)
        self.z          = 0.0   # posición Z en mm
        self._z_step_mm = 1.0   # mm que se mueve por clic en los botones Z

        # Trayectoria completa (todos los puntos recibidos)
        self._trail_x: deque = deque(maxlen=MAX_TRAIL_PTS)
        self._trail_y: deque = deque(maxlen=MAX_TRAIL_PTS)

        # Segmento actual de captura activa
        self._capture_x: list = []
        self._capture_y: list = []

        # Historial de segmentos capturados (para DXF)
        self._segments: List[List[Tuple[float, float]]] = []

        # Punto de inicio para trazar líneas rectas (None = espera 1er clic)
        # ELIMINADO – sustituido por la herramienta de polilínea

        # Lista de líneas rectas trazadas: [(x0,y0), (x1,y1)]
        self._straight_lines: List[Tuple[Tuple[float, float],
                                         Tuple[float, float]]] = []

        # ── Herramienta de polilínea ────────────────────────────────────────
        # Nodos añadidos en la sesión actual (en construcción)
        self._polyline_pts: List[Tuple[float, float]] = []
        # Nodo al que se haría snap (calculado en _animate, sin lock)
        self._snap_candidate: Optional[Tuple[float, float]] = None

        # ── Herramienta de arco (3 puntos) ─────────────────────────────────
        # Puntos de la sesión actual: P1 (inicio), P2 (referencia), P3 (fin)
        self._arc_pts: List[Tuple[float, float]] = []
        # Arcos comprometidos: cada elemento es una lista de (x, y) de la curva
        self._arcs: List[List[Tuple[float, float]]] = []

        # Lista de círculos timbrados: [(cx, cy), ...]
        self._stamp_circles: List[Tuple[float, float]] = []

        # Radio actual del círculo timbrado (controlado por el TextBox de diámetro)
        self._stamp_radius_mm: float = DEFAULT_STAMP_RADIUS_MM  # 5 mm = diámetro 1 cm

        # ── Herramienta círculo por 3 puntos ───────────────────────────────
        # Puntos de la sesión actual (hasta 3 puntos en la circunferencia)
        self._circle3p_pts: List[Tuple[float, float]] = []
        # Círculos comprometidos: (cx, cy, r)
        self._circle3p_circles: List[Tuple[float, float, float]] = []

        # Visibilidad de la trayectoria fantasma (trail)
        self._trail_visible: bool = True

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

        ax_btn_start    = self.fig.add_axes([0.76, 0.816, 0.21, 0.038])
        ax_btn_stop     = self.fig.add_axes([0.76, 0.774, 0.21, 0.038])
        ax_btn_clear    = self.fig.add_axes([0.76, 0.732, 0.21, 0.038])
        ax_btn_export   = self.fig.add_axes([0.76, 0.690, 0.21, 0.038])
        ax_btn_home     = self.fig.add_axes([0.76, 0.648, 0.21, 0.038])
        ax_btn_reset    = self.fig.add_axes([0.76, 0.606, 0.21, 0.038])
        ax_btn_poly_add = self.fig.add_axes([0.76, 0.564, 0.21, 0.038])
        ax_btn_poly_end = self.fig.add_axes([0.76, 0.522, 0.21, 0.038])
        ax_btn_arc_add  = self.fig.add_axes([0.76, 0.480, 0.21, 0.038])
        ax_btn_circle   = self.fig.add_axes([0.76, 0.438, 0.21, 0.038])
        ax_btn_circle3p = self.fig.add_axes([0.76, 0.396, 0.21, 0.038])
        ax_btn_trail    = self.fig.add_axes([0.76, 0.354, 0.21, 0.038])
        # Botones Z: mitad de ancho, misma fila
        ax_btn_z_up     = self.fig.add_axes([0.76,   0.312, 0.105, 0.038])
        ax_btn_z_down   = self.fig.add_axes([0.865,  0.312, 0.105, 0.038])

        self.btn_start    = Button(ax_btn_start,    "▶ Iniciar Captura",  **btn_cfg)
        self.btn_stop     = Button(ax_btn_stop,     "■ Detener Captura",  **btn_cfg)
        self.btn_clear    = Button(ax_btn_clear,    "✖ Limpiar",          **btn_cfg)
        self.btn_export   = Button(ax_btn_export,   "⬇ Exportar DXF",    **btn_cfg)
        self.btn_home     = Button(ax_btn_home,     "⌂ Home",             **btn_cfg)
        self.btn_reset    = Button(ax_btn_reset,    "↺ Reset (↑)",        **btn_cfg)
        self.btn_poly_add = Button(ax_btn_poly_add, "✦ Añadir Punto",     **btn_cfg)
        self.btn_poly_end = Button(ax_btn_poly_end, "⬛ Fin Polilínea",   **btn_cfg)
        self.btn_arc_add  = Button(ax_btn_arc_add,  "◜ Punto Arco",       **btn_cfg)
        self.btn_circle   = Button(ax_btn_circle,   "⊙ Círculo 1.0 cm",  **btn_cfg)
        self.btn_circle3p = Button(ax_btn_circle3p, "⊙ Círculo 3P",      **btn_cfg)
        self.btn_trail    = Button(ax_btn_trail,    "👁 Trayectoria ✓",   **btn_cfg)
        self.btn_z_up     = Button(ax_btn_z_up,     "▲ Subir Z",          **btn_cfg)
        self.btn_z_down   = Button(ax_btn_z_down,   "▼ Bajar Z",          **btn_cfg)

        for btn in (self.btn_start, self.btn_stop, self.btn_clear,
                    self.btn_export, self.btn_home, self.btn_reset,
                    self.btn_poly_add, self.btn_poly_end,
                    self.btn_arc_add, self.btn_circle,
                    self.btn_circle3p, self.btn_trail,
                    self.btn_z_up, self.btn_z_down):
            btn.label.set_color("white")
            btn.label.set_fontsize(9)

        self.btn_start   .on_clicked(self._on_start)
        self.btn_stop    .on_clicked(self._on_stop)
        self.btn_clear   .on_clicked(self._on_clear)
        self.btn_export  .on_clicked(self._on_export)
        self.btn_home    .on_clicked(self._on_home)
        self.btn_reset   .on_clicked(self._on_reset)
        self.btn_poly_add.on_clicked(self._on_poly_add)
        self.btn_poly_end.on_clicked(self._on_poly_end)
        self.btn_arc_add .on_clicked(self._on_arc_add)
        self.btn_circle  .on_clicked(self._on_circle)
        self.btn_circle3p.on_clicked(self._on_circle3p)
        self.btn_trail   .on_clicked(self._on_toggle_trail)
        self.btn_z_up    .on_clicked(self._on_z_up)
        self.btn_z_down  .on_clicked(self._on_z_down)

        # ── TextBox para diámetro del círculo timbrado ──────────────────
        ax_diam_lbl = self.fig.add_axes([0.76, 0.274, 0.08, 0.034])
        ax_diam_box = self.fig.add_axes([0.86, 0.274, 0.11, 0.034])
        ax_diam_lbl.set_facecolor("#1e2130"); ax_diam_lbl.axis("off")
        ax_diam_lbl.text(0.5, 0.5, "Diám (cm)", ha="center", va="center",
                         color="#44ffcc", fontsize=8)
        self.tb_diam = TextBox(ax_diam_box, "", initial="1.0",
                               color="#2a2d3e", hovercolor="#3a3f5c")
        self.tb_diam.label.set_color("#44ffcc")
        self.tb_diam.on_submit(self._on_circle_diam_change)

        # ── TextBox para el paso del eje Z ──────────────────────────────
        ax_zstep_lbl = self.fig.add_axes([0.76, 0.236, 0.08, 0.034])
        ax_zstep_box = self.fig.add_axes([0.86, 0.236, 0.11, 0.034])
        ax_zstep_lbl.set_facecolor("#1e2130"); ax_zstep_lbl.axis("off")
        ax_zstep_lbl.text(0.5, 0.5, "Paso Z mm", ha="center", va="center",
                          color="#88ddff", fontsize=8)
        self.tb_zstep = TextBox(ax_zstep_box, "", initial=str(self._z_step_mm),
                                color="#2a2d3e", hovercolor="#3a3f5c")
        self.tb_zstep.label.set_color("#88ddff")
        self.tb_zstep.on_submit(self._on_z_step_change)

        # ── TextBox para L1, L2, G1, G2 ────────────────────────────────
        ax_l1_lbl = self.fig.add_axes([0.76, 0.198, 0.09, 0.034])
        ax_l1_box = self.fig.add_axes([0.86, 0.198, 0.11, 0.034])
        ax_l2_lbl = self.fig.add_axes([0.76, 0.160, 0.09, 0.034])
        ax_l2_box = self.fig.add_axes([0.86, 0.160, 0.11, 0.034])
        ax_g1_lbl = self.fig.add_axes([0.76, 0.122, 0.09, 0.034])
        ax_g1_box = self.fig.add_axes([0.86, 0.122, 0.11, 0.034])
        ax_g2_lbl = self.fig.add_axes([0.76, 0.084, 0.09, 0.034])
        ax_g2_box = self.fig.add_axes([0.86, 0.084, 0.11, 0.034])

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
        ax_info = self.fig.add_axes([0.76, 0.030, 0.21, 0.050],
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
        # ── Herramienta de polilínea ───────────────────────────────────────
        # Línea de vista previa (en construcción, desde el primer nodo hasta EE)
        self._line_poly_preview, = self.ax.plot([], [], "--", color="#ff44ff",
                                                linewidth=1.5, alpha=0.7)
        # Marcadores de nodos añadidos
        self._dot_poly_pts, = self.ax.plot([], [], "o", color="#ff44ff",
                                           markersize=7, markerfacecolor="#ff44ff",
                                           label="Nodos polilínea")
        # Indicador de snap (anillo amarillo sobre el nodo objetivo)
        self._dot_snap, = self.ax.plot([], [], "o", color="#ffff00",
                                       markersize=16, markerfacecolor="none",
                                       markeredgewidth=2.5)
        # Círculos timbrados (⊙ diámetro ajustable), curvas paramétricas separadas por NaN
        self._line_circles, = self.ax.plot([], [], "-", color="#44ffcc",
                                           linewidth=1.5, alpha=0.9,
                                           label="Círculos stamp")
        # Círculos por 3 puntos (separados por NaN)
        self._line_circle3p, = self.ax.plot([], [], "-", color="#ffaa22",
                                            linewidth=1.5, alpha=0.9,
                                            label="Círculos 3P")
        # Vista previa del círculo 3P en construcción (puntos de referencia)
        self._dot_circle3p_pts, = self.ax.plot([], [], "D", color="#ffaa22",
                                               markersize=7,
                                               markerfacecolor="#ffaa22",
                                               label="Pts círculo 3P")
        # ── Herramienta de arco ────────────────────────────────────────────
        # Arcos comprometidos (separados por NaN)
        self._line_arcs, = self.ax.plot([], [], "-", color="#44aaff",
                                        linewidth=2.0, alpha=0.9,
                                        label="Arcos")
        # Vista previa del arco en construcción
        self._line_arc_preview, = self.ax.plot([], [], "--", color="#44aaff",
                                               linewidth=1.5, alpha=0.7)
        # Puntos de referencia del arco en construcción
        self._dot_arc_pts, = self.ax.plot([], [], "D", color="#44aaff",
                                          markersize=7, markerfacecolor="#44aaff",
                                          label="Pts arco")

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
        """Analiza una línea del formato 'X:v,Y:v,T1:v,T2:v[,Z:v]'."""
        try:
            parts = {p.split(":")[0]: float(p.split(":")[1])
                     for p in line.split(",") if ":" in p}
            x  = parts.get("X", self.x)
            y  = parts.get("Y", self.y)
            t1 = parts.get("T1", self.theta1)
            t2 = parts.get("T2", self.theta2)
            z  = parts.get("Z", self.z)
        except (ValueError, IndexError):
            return

        with self._serial_lock:
            self.x = x
            self.y = y
            self.theta1 = t1
            self.theta2 = t2
            self.z = z
            self._trail_x.append(x)
            self._trail_y.append(y)
            self._total_points += 1
            if self._capturing:
                self._capture_x.append(x)
                self._capture_y.append(y)
                self._captured_count += 1

    # ── Herramienta de arco – cálculo geométrico ─────────────────────────
    @staticmethod
    def _compute_arc_pts(p1: Tuple[float, float],
                         p2: Tuple[float, float],
                         p3: Tuple[float, float],
                         n_pts: int = 64) -> List[Tuple[float, float]]:
        """Devuelve n_pts puntos del arco de circunferencia que pasa por
        p1 → p2 → p3 (p2 es el punto intermedio de referencia).

        Si los tres puntos son colineales se devuelven los propios puntos
        en lugar de un arco.
        """
        (ax_c, ay_c), (bx, by), (cx_c, cy_c) = p1, p2, p3
        D = 2.0 * (ax_c * (by - cy_c) + bx * (cy_c - ay_c) + cx_c * (ay_c - by))
        if abs(D) < COLLINEARITY_EPSILON:   # puntos colineales → segmento recto
            return [p1, p2, p3]

        ux = ((ax_c**2 + ay_c**2) * (by - cy_c) +
              (bx**2  + by**2)    * (cy_c - ay_c) +
              (cx_c**2 + cy_c**2) * (ay_c - by)) / D
        uy = ((ax_c**2 + ay_c**2) * (cx_c - bx) +
              (bx**2  + by**2)    * (ax_c - cx_c) +
              (cx_c**2 + cy_c**2) * (bx - ax_c)) / D
        r = math.hypot(ax_c - ux, ay_c - uy)

        a1 = math.atan2(ay_c - uy, ax_c - ux)
        a2 = math.atan2(by   - uy, bx   - ux)
        a3 = math.atan2(cy_c - uy, cx_c - ux)

        # Determinar dirección: ver si a2 cae entre a1 y a3 en sentido CCW
        def _ccw_sweep(start: float, end: float) -> float:
            d = (end - start) % (2 * math.pi)
            return d

        sweep_to_2 = _ccw_sweep(a1, a2)
        sweep_to_3 = _ccw_sweep(a1, a3)

        if sweep_to_2 < sweep_to_3:   # CCW: a1 → a2 → a3
            angles = np.linspace(a1, a1 + sweep_to_3, n_pts)
        else:                          # CW: a1 → a2 → a3 en sentido horario
            sweep_to_3_cw = sweep_to_3 - 2 * math.pi  # negativo
            angles = np.linspace(a1, a1 + sweep_to_3_cw, n_pts)

        xs = ux + r * np.cos(angles)
        ys = uy + r * np.sin(angles)
        return list(zip(xs.tolist(), ys.tolist()))

    # ── Animación ─────────────────────────────────────────────────────────
    def _animate(self, _frame):
        with self._serial_lock:
            tx = list(self._trail_x)
            ty = list(self._trail_y)
            cx = list(self._capture_x)
            cy = list(self._capture_y)
            x, y = self.x, self.y
            t1, t2 = self.theta1, self.theta2
            z = self.z
            sl = list(self._straight_lines)
            poly = list(self._polyline_pts)
            arcs = list(self._arcs)
            arc_pts = list(self._arc_pts)
            sc = list(self._stamp_circles)
            c3p = list(self._circle3p_circles)
            c3p_pts = list(self._circle3p_pts)
            stamp_r = self._stamp_radius_mm

        # Trayectoria completa
        if self._trail_visible:
            self._line_trail.set_data(tx, ty)
            self._line_trail.set_visible(True)
        else:
            self._line_trail.set_visible(False)

        # Captura activa
        self._line_capture.set_data(cx, cy)

        # Esqueleto del robot
        ex, ey = self._elbow_pos(t1)
        self._line_link1.set_data([0, ex], [0, ey])
        self._line_link2.set_data([ex, x], [ey, y])
        self._dot_ee.set_data([x], [y])

        # Líneas rectas finalizadas (usando NaN como separador de segmentos)
        if sl:
            nan = float("nan")
            xs, ys = [], []
            for (x0, y0), (x1, y1) in sl:
                xs += [x0, x1, nan]
                ys += [y0, y1, nan]
            self._line_straight_all.set_data(xs, ys)
        else:
            self._line_straight_all.set_data([], [])

        # ── Herramienta de polilínea en construcción ───────────────────────
        # Calcular snap: primer nodo dentro de SNAP_RADIUS
        snap = None
        if poly:
            for pt in poly:
                if math.hypot(x - pt[0], y - pt[1]) <= SNAP_RADIUS:
                    snap = pt
                    break
        self._snap_candidate = snap

        if poly:
            preview_end = snap if snap is not None else (x, y)
            pxs = [p[0] for p in poly] + [preview_end[0]]
            pys = [p[1] for p in poly] + [preview_end[1]]
            self._line_poly_preview.set_data(pxs, pys)
            self._dot_poly_pts.set_data([p[0] for p in poly],
                                        [p[1] for p in poly])
        else:
            self._line_poly_preview.set_data([], [])
            self._dot_poly_pts.set_data([], [])

        if snap is not None:
            self._dot_snap.set_data([snap[0]], [snap[1]])
        else:
            self._dot_snap.set_data([], [])

        # ── Herramienta de arco ────────────────────────────────────────────
        # Arcos comprometidos
        if arcs:
            nan = float("nan")
            axs, ays = [], []
            for curve in arcs:
                axs += [p[0] for p in curve] + [nan]
                ays += [p[1] for p in curve] + [nan]
            self._line_arcs.set_data(axs, ays)
        else:
            self._line_arcs.set_data([], [])

        # Vista previa del arco en construcción
        if arc_pts:
            pts_with_ee = arc_pts + [(x, y)]
            if len(pts_with_ee) == 2:
                # Solo P1 + EE: mostrar línea recta provisional
                self._line_arc_preview.set_data(
                    [pts_with_ee[0][0], pts_with_ee[1][0]],
                    [pts_with_ee[0][1], pts_with_ee[1][1]]
                )
            elif len(pts_with_ee) >= 3:
                # P1, P2 y EE como P3 provisional: mostrar arco
                preview_curve = self._compute_arc_pts(
                    pts_with_ee[0], pts_with_ee[1], pts_with_ee[2]
                )
                self._line_arc_preview.set_data(
                    [p[0] for p in preview_curve],
                    [p[1] for p in preview_curve]
                )
            self._dot_arc_pts.set_data(
                [p[0] for p in arc_pts],
                [p[1] for p in arc_pts]
            )
        else:
            self._line_arc_preview.set_data([], [])
            self._dot_arc_pts.set_data([], [])

        # Círculos timbrados (curvas paramétricas separadas por NaN)
        if sc:
            nan = float("nan")
            theta_pts = np.linspace(0, 2 * math.pi, 64)
            cxs, cys = [], []
            for (ccx, ccy) in sc:
                cxs += list(ccx + stamp_r * np.cos(theta_pts)) + [nan]
                cys += list(ccy + stamp_r * np.sin(theta_pts)) + [nan]
            self._line_circles.set_data(cxs, cys)
        else:
            self._line_circles.set_data([], [])

        # Círculos por 3 puntos comprometidos
        if c3p:
            nan = float("nan")
            theta_pts = np.linspace(0, 2 * math.pi, 128)
            c3xs, c3ys = [], []
            for (ccx, ccy, cr) in c3p:
                c3xs += list(ccx + cr * np.cos(theta_pts)) + [nan]
                c3ys += list(ccy + cr * np.sin(theta_pts)) + [nan]
            self._line_circle3p.set_data(c3xs, c3ys)
        else:
            self._line_circle3p.set_data([], [])

        # Puntos de referencia del círculo 3P en construcción
        if c3p_pts:
            self._dot_circle3p_pts.set_data(
                [p[0] for p in c3p_pts],
                [p[1] for p in c3p_pts]
            )
        else:
            self._dot_circle3p_pts.set_data([], [])

        # Panel informativo
        self._info_text.set_text(self._info_str(x, y, t1, t2, z))

        return (self._line_trail, self._line_capture,
                self._line_link1, self._line_link2,
                self._dot_ee, self._line_straight_all,
                self._line_poly_preview, self._dot_poly_pts,
                self._dot_snap, self._line_arcs,
                self._line_arc_preview, self._dot_arc_pts,
                self._line_circles, self._line_circle3p,
                self._dot_circle3p_pts, self._info_text)

    def _info_str(self, x=None, y=None, t1=None, t2=None, z=None) -> str:
        x  = x  if x  is not None else self.x
        y  = y  if y  is not None else self.y
        t1 = t1 if t1 is not None else self.theta1
        t2 = t2 if t2 is not None else self.theta2
        z  = z  if z  is not None else self.z

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
            f"Z:{z:+7.1f}mm\n"
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
            self._stamp_circles  = []
            self._polyline_pts   = []
            self._arc_pts        = []
            self._arcs           = []
            self._circle3p_pts   = []
            self._circle3p_circles = []
        self._snap_candidate = None
        self._set_status("Trayectoria limpiada")

    def _on_export(self, _event):
        if not EZDXF_AVAILABLE:
            self._set_status("ERROR: ezdxf no instalado – no se puede exportar")
            return

        with self._serial_lock:
            segments = [list(s) for s in self._segments]
            straight = list(self._straight_lines)
            circles  = list(self._stamp_circles)
            arcs     = list(self._arcs)
            c3p      = list(self._circle3p_circles)
            # También incluir captura activa si tiene puntos
            if self._capture_x and len(self._capture_x) >= 2:
                segments.append(list(zip(self._capture_x, self._capture_y)))

        if not segments and not straight and not circles and not arcs and not c3p:
            self._set_status("Sin trayectoria capturada para exportar")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scara_trajectory_{ts}.dxf"
        try:
            self._export_dxf(segments, straight, circles, filename, arcs, c3p)
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

    def _on_poly_add(self, _event):
        """Añade el punto actual del efector a la polilínea en construcción.

        Si el snap está activo (EE cerca de un nodo existente), el nuevo punto
        se ancla exactamente a ese nodo, permitiendo cerrar figuras con precisión.
        Cada nuevo punto se conecta automáticamente al anterior con una línea recta.
        """
        with self._serial_lock:
            x, y = self.x, self.y

        snap = self._snap_candidate
        pos = snap if snap is not None else (x, y)

        with self._serial_lock:
            pts = self._polyline_pts
            if pts:
                # Conectar al punto anterior
                self._straight_lines.append((pts[-1], pos))
                self._segments.append([pts[-1], pos])
            pts.append(pos)
            n = len(pts)

        if snap is not None:
            self._set_status(
                f"⊕ Snap → ({snap[0]:.1f}, {snap[1]:.1f}) – {n} nodo(s)"
            )
        else:
            self._set_status(
                f"✦ Punto {n} añadido ({pos[0]:.1f}, {pos[1]:.1f})"
            )

    def _on_poly_end(self, _event):
        """Finaliza la herramienta de polilínea y descarta la sesión actual."""
        with self._serial_lock:
            n = len(self._polyline_pts)
            self._polyline_pts = []
        self._snap_candidate = None
        self._set_status(
            f"⬛ Polilínea finalizada – {n} nodo(s), "
            f"{max(0, n - 1)} segmento(s) guardado(s)"
        )

    def _on_arc_add(self, _event):
        """Añade el punto actual a la herramienta de arco de 3 puntos.

        1er clic → P1 (inicio del arco)
        2do clic → P2 (punto de referencia intermedio)
        3er clic → P3 (fin del arco) → el arco se calcula y se compromete;
                   el estado se reinicia para trazar otro arco.
        """
        with self._serial_lock:
            x, y = self.x, self.y

        with self._serial_lock:
            self._arc_pts.append((x, y))
            n = len(self._arc_pts)

        labels = {1: "P1 inicio", 2: "P2 referencia", 3: "P3 fin"}
        self._set_status(
            f"◜ Arco {labels[n]}: ({x:.1f}, {y:.1f})"
            + (" – añade P2" if n == 1 else
               " – añade P3" if n == 2 else "")
        )

        if n == 3:
            with self._serial_lock:
                pts = list(self._arc_pts)
                self._arc_pts = []

            curve = self._compute_arc_pts(pts[0], pts[1], pts[2])
            with self._serial_lock:
                self._arcs.append(curve)
            self._set_status(
                f"◜ Arco comprometido: P1({pts[0][0]:.1f},{pts[0][1]:.1f}) "
                f"P2({pts[1][0]:.1f},{pts[1][1]:.1f}) "
                f"P3({pts[2][0]:.1f},{pts[2][1]:.1f})"
            )

    def _on_circle(self, _event):
        """Timbra un círculo de diámetro ajustable centrado en el efector final."""
        with self._serial_lock:
            x, y = self.x, self.y
        with self._serial_lock:
            self._stamp_circles.append((x, y))
        diam_cm = self._stamp_radius_mm * 2 / 10.0
        self._set_status(
            f"⊙ Círculo {diam_cm:.2g} cm añadido en ({x:.1f}, {y:.1f}) mm"
        )

    def _on_circle_diam_change(self, text: str):
        """Actualiza el radio del círculo timbrado desde el TextBox (valor en cm)."""
        try:
            diam_cm = float(text)
            if diam_cm <= 0:
                raise ValueError("El diámetro debe ser positivo")
            self._stamp_radius_mm = diam_cm / 2.0 * 10.0  # cm → mm radio
            self.btn_circle.label.set_text(f"⊙ Círculo {diam_cm:.2g} cm")
            self.fig.canvas.draw_idle()
            self._set_status(f"⊙ Diámetro círculo actualizado → {diam_cm:.2g} cm")
        except ValueError:
            self._set_status("ERROR: Diámetro debe ser un número positivo en cm")

    def _on_circle3p(self, _event):
        """Herramienta círculo por 3 puntos.

        1er clic → P1 (inicio y cierre del círculo, en la circunferencia)
        2do clic → P2 (otro punto de la circunferencia)
        3er clic → P3 (último punto); se calcula y compromete el círculo.
        """
        with self._serial_lock:
            x, y = self.x, self.y

        with self._serial_lock:
            self._circle3p_pts.append((x, y))
            n = len(self._circle3p_pts)

        labels = {1: "P1 (inicio/cierre)", 2: "P2", 3: "P3 (fin)"}
        self._set_status(
            f"⊙ 3P {labels[n]}: ({x:.1f}, {y:.1f})"
            + (" – añade P2" if n == 1 else " – añade P3" if n == 2 else "")
        )

        if n == 3:
            with self._serial_lock:
                pts = list(self._circle3p_pts)
                self._circle3p_pts = []

            result = self._circle_from_3_points(pts[0], pts[1], pts[2])
            if result is not None:
                cx, cy, r = result
                with self._serial_lock:
                    self._circle3p_circles.append((cx, cy, r))
                self._set_status(
                    f"⊙ Círculo 3P: centro ({cx:.1f},{cy:.1f}) r={r:.1f} mm"
                )
            else:
                self._set_status(
                    "⊙ Los 3 puntos son colineales – no se puede trazar un círculo"
                )

    @staticmethod
    def _circle_from_3_points(
            p1: Tuple[float, float],
            p2: Tuple[float, float],
            p3: Tuple[float, float]
    ) -> Optional[Tuple[float, float, float]]:
        """Calcula el círculo que pasa exactamente por los 3 puntos dados.

        Devuelve (cx, cy, r) o None si los puntos son colineales.
        """
        (x1, y1), (x2, y2), (x3, y3) = p1, p2, p3
        D = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        if abs(D) < COLLINEARITY_EPSILON:
            return None
        ux = ((x1**2 + y1**2) * (y2 - y3) +
              (x2**2 + y2**2) * (y3 - y1) +
              (x3**2 + y3**2) * (y1 - y2)) / D
        uy = ((x1**2 + y1**2) * (x3 - x2) +
              (x2**2 + y2**2) * (x1 - x3) +
              (x3**2 + y3**2) * (x2 - x1)) / D
        r = math.hypot(x1 - ux, y1 - uy)
        return ux, uy, r

    def _on_toggle_trail(self, _event):
        """Alterna la visibilidad de la trayectoria fantasma de seguimiento."""
        self._trail_visible = not self._trail_visible
        label = "👁 Trayectoria ✓" if self._trail_visible else "👁 Trayectoria ✗"
        self.btn_trail.label.set_text(label)
        self.fig.canvas.draw_idle()
        state = "visible" if self._trail_visible else "oculta"
        self._set_status(f"Trayectoria fantasma {state}")

    def _on_z_up(self, _event):
        """Envía comando ZU al Arduino para subir el eje Z un paso."""
        step = self._z_step_mm
        if self._serial and self._serial_ok:
            try:
                self._serial.write(f"ZU:{step:.2f}\n".encode())
            except Exception as exc:
                self._set_status(f"ERROR enviando ZU: {exc}")
                return
            with self._serial_lock:
                self.z += step
            self._set_status(f"▲ Z subido {step:.2f} mm → {self.z:.1f} mm")
        else:
            self._set_status("ERROR: Arduino no conectado – ZU no enviado")

    def _on_z_down(self, _event):
        """Envía comando ZD al Arduino para bajar el eje Z un paso."""
        step = self._z_step_mm
        if self._serial and self._serial_ok:
            try:
                self._serial.write(f"ZD:{step:.2f}\n".encode())
            except Exception as exc:
                self._set_status(f"ERROR enviando ZD: {exc}")
                return
            with self._serial_lock:
                self.z -= step
            self._set_status(f"▼ Z bajado {step:.2f} mm → {self.z:.1f} mm")
        else:
            self._set_status("ERROR: Arduino no conectado – ZD no enviado")

    def _on_z_step_change(self, text: str):
        """Actualiza el paso Z (mm por clic) desde el TextBox."""
        try:
            val = float(text)
            if val > 0:
                self._z_step_mm = val
                self._set_status(f"Paso Z → {val:.2f} mm/clic")
            else:
                self._set_status("ERROR: Paso Z debe ser > 0")
        except ValueError:
            self._set_status("ERROR: Paso Z debe ser un número positivo")

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
    def _export_dxf(self, segments: list, straight_lines: list,
                    stamp_circles: list, filename: str, arcs: list = None,
                    circle3p_circles: list = None):
        """Genera un archivo DXF con las trayectorias capturadas.

        Todos los trazos se exportan con color uniforme (ACI 7 – blanco/negro CNC).
        La trayectoria fantasma de seguimiento NO se incluye en el DXF.
        """
        if arcs is None:
            arcs = []
        if circle3p_circles is None:
            circle3p_circles = []
        doc = ezdxf.new(dxfversion="R2010")
        doc.units = dxf_units.MM

        # Color uniforme (ACI 7 = blanco/negro estándar CNC) para todas las capas
        UNIFORM_COLOR = 7

        # Capas
        doc.layers.new(name="TRAJECTORY",
                       dxfattribs={"color": UNIFORM_COLOR, "linetype": "CONTINUOUS"})
        doc.layers.new(name="STRAIGHT_LINES",
                       dxfattribs={"color": UNIFORM_COLOR, "linetype": "CONTINUOUS"})
        doc.layers.new(name="CIRCLES",
                       dxfattribs={"color": UNIFORM_COLOR, "linetype": "CONTINUOUS"})
        doc.layers.new(name="ARCS",
                       dxfattribs={"color": UNIFORM_COLOR, "linetype": "CONTINUOUS"})
        doc.layers.new(name="CIRCLE3P",
                       dxfattribs={"color": UNIFORM_COLOR, "linetype": "CONTINUOUS"})
        doc.layers.new(name="METADATA",
                       dxfattribs={"color": UNIFORM_COLOR, "linetype": "CONTINUOUS"})

        msp = doc.modelspace()

        for seg in segments:
            if len(seg) < 2:
                continue
            pts = [(float(p[0]), float(p[1])) for p in seg]
            msp.add_lwpolyline(pts, close=False,
                               dxfattribs={"layer": "TRAJECTORY",
                                           "color": UNIFORM_COLOR})

        for (x0, y0), (x1, y1) in straight_lines:
            msp.add_line((float(x0), float(y0)), (float(x1), float(y1)),
                         dxfattribs={"layer": "STRAIGHT_LINES",
                                     "color": UNIFORM_COLOR})

        for (ccx, ccy) in stamp_circles:
            msp.add_circle((float(ccx), float(ccy)), self._stamp_radius_mm,
                           dxfattribs={"layer": "CIRCLES", "color": UNIFORM_COLOR})

        for curve in arcs:
            if len(curve) < 2:
                continue
            pts = [(float(p[0]), float(p[1])) for p in curve]
            msp.add_lwpolyline(pts, close=False,
                               dxfattribs={"layer": "ARCS", "color": UNIFORM_COLOR})

        for (ccx, ccy, cr) in circle3p_circles:
            msp.add_circle((float(ccx), float(ccy)), float(cr),
                           dxfattribs={"layer": "CIRCLE3P", "color": UNIFORM_COLOR})

        # Texto de metadatos
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = (
            f"Generado: {ts}  |  "
            f"L1={self.L1:.1f}mm  L2={self.L2:.1f}mm  |  "
            f"Segmentos={len(segments)}  Líneas rectas={len(straight_lines)}  "
            f"Círculos stamp={len(stamp_circles)}  Arcos={len(arcs)}  "
            f"Círculos 3P={len(circle3p_circles)}"
        )
        msp.add_text(
            metadata,
            dxfattribs={
                "layer": "METADATA",
                "height": 2.0,
                "insert": (0, -(self.L1 + self.L2) * 1.2),
                "color": UNIFORM_COLOR,
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
