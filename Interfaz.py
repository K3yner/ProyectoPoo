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


# Componentes reutilizables

class TarjetaNivel(tk.Frame):
    """Tarjeta que muestra cuántos registros hay en un nivel."""

    def __init__(self, master, tema, nivel):
        super().__init__(master, bg=tema.superficie,
                         highlightbackground=tema.borde, highlightthickness=1)
        self.__tema = tema
        color = tema.color_nivel(nivel)

        tk.Frame(self, bg=color, height=5).pack(fill="x")
        tk.Label(self, text=nivel.upper(), bg=tema.superficie, fg=color,
                 font=(tema.fuente, 11, "bold")).pack(pady=(10, 0))
        self.__valor = tk.Label(self, text="0", bg=tema.superficie, fg=tema.texto,
                                font=(tema.fuente, 30, "bold"))
        self.__valor.pack()
        self.__porcentaje = tk.Label(self, text="0 %", bg=tema.superficie,
                                     fg=tema.texto_suave, font=(tema.fuente, 10))
        self.__porcentaje.pack(pady=(0, 10))

    def actualizar(self, cantidad, total):
        self.__valor.config(text=str(cantidad))
        pct = (cantidad / total * 100) if total else 0
        self.__porcentaje.config(text=f"{pct:.1f} %")


class PanelLog(tk.Frame):
    """Cuadro de texto de solo lectura para mensajes del sistema."""

    def __init__(self, master, tema):
        super().__init__(master, bg=tema.fondo)
        tk.Label(self, text="Mensajes", bg=tema.fondo, fg=tema.texto,
                 font=(tema.fuente, 12, "bold")).pack(anchor="w", pady=(0, 6))
        self.__texto = tk.Text(self, height=5, bg=tema.superficie_alt, fg=tema.texto,
                               insertbackground=tema.texto, relief="flat",
                               font=(tema.fuente_mono, 9), state="disabled",
                               highlightbackground=tema.borde, highlightthickness=1)
        self.__texto.pack(fill="both", expand=True)

    def escribir(self, mensaje):
        self.__texto.config(state="normal")
        self.__texto.insert("end", mensaje.rstrip() + "\n")
        self.__texto.see("end")
        self.__texto.config(state="disabled")
