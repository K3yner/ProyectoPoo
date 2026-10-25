"""
interfaz.py

Interfaz gráfica (tkinter) para el monitor de vibraciones.

Solo se encarga de mostrar información y de llamar a los métodos públicos del
Controlador (iniciar_medicion, detener_medicion, obtener_resumen). No contiene
lógica de clasificación ni de comunicación con phyphox.

Los colores y las fuentes viven en la clase Tema: para cambiar el aspecto de
toda la interfaz basta con editar los atributos de Tema (o pasar una instancia
modificada a InterfazVibraciones).

Ejecutar:  python interfaz.py
"""

import io
import math
import os
import queue
import tkinter as tk
from contextlib import redirect_stdout
from tkinter import ttk, messagebox


# ----------------------------------------------------------------------
# Tema: TODOS los colores y fuentes de la interfaz están aquí
# ----------------------------------------------------------------------
class Tema:
    """Guarda los colores y fuentes de la interfaz como atributos editables."""

    def __init__(self):
        # Fondos
        self.fondo = "#0F172A"          # fondo de la ventana
        self.superficie = "#1E293B"     # tarjetas y paneles
        self.superficie_alt = "#273449" # filas alternas / campos de texto
        self.borde = "#334155"

        # Texto
        self.texto = "#F1F5F9"
        self.texto_suave = "#94A3B8"

        # Acento general
        self.acento = "#38BDF8"

        # Niveles de vibración
        self.nivel_baja = "#22C55E"
        self.nivel_media = "#FACC15"
        self.nivel_alta = "#EF4444"

        # Botones
        self.boton_iniciar = "#16A34A"
        self.boton_detener = "#DC2626"
        self.boton_neutro = "#475569"
        self.boton_texto = "#FFFFFF"
        self.boton_desactivado = "#334155"

        # Estado de la medición
        self.estado_activo = "#EF4444"
        self.estado_inactivo = "#64748B"

        # Fuentes
        self.fuente = "Segoe UI"
        self.fuente_mono = "Consolas"

    def color_nivel(self, nivel):
        """Devuelve el color asociado a 'alta', 'media' o 'baja'."""
        return {
            "alta": self.nivel_alta,
            "media": self.nivel_media,
            "baja": self.nivel_baja,
        }.get(nivel, self.texto_suave)
