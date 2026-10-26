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

class GraficoMagnitudes(tk.Canvas):
    """Gráfico de línea de las magnitudes, con las líneas de los umbrales."""

    MARGEN = 40
    MAX_PUNTOS = 800

    def __init__(self, master, tema):
        super().__init__(master, bg=tema.superficie, highlightthickness=1,
                         highlightbackground=tema.borde, height=300)
        self.__tema = tema
        self.__magnitudes = []
        self.__limite_medio = 1.5
        self.__limite_alto = 3.0
        self.bind("<Configure>", lambda _e: self._dibujar())

    def actualizar(self, magnitudes, limite_medio, limite_alto):
        self.__magnitudes = list(magnitudes)
        self.__limite_medio = limite_medio
        self.__limite_alto = limite_alto
        self._dibujar()

    def _dibujar(self):
        t = self.__tema
        self.delete("all")
        w, h, m = self.winfo_width(), self.winfo_height(), self.MARGEN
        if w < 100 or h < 100:
            return

        datos = self.__magnitudes
        if not datos:
            self.create_text(w / 2, h / 2, text="Sin datos todavía",
                             fill=t.texto_suave, font=(t.fuente, 12))
            return

        paso = max(1, math.ceil(len(datos) / self.MAX_PUNTOS))
        datos = datos[::paso]
        y_max = max(max(datos), self.__limite_alto) * 1.15

        def px(i):
            return m + (w - 2 * m) * (i / max(1, len(datos) - 1))

        def py(valor):
            return h - m + 10 - (h - 2 * m) * (valor / y_max)

        # Ejes
        self.create_line(m, m - 10, m, h - m + 10, fill=t.borde)
        self.create_line(m, h - m + 10, w - m, h - m + 10, fill=t.borde)

        # Umbrales
        for valor, nivel, nombre in ((self.__limite_medio, "media", "media"),
                                     (self.__limite_alto, "alta", "alta")):
            y = py(valor)
            color = t.color_nivel(nivel)
            self.create_line(m, y, w - m, y, fill=color, dash=(4, 4))
            self.create_text(w - m, y - 8, text=f"{nombre} ({valor})",
                             fill=color, anchor="e", font=(t.fuente, 8))

        # Etiquetas del eje Y
        self.create_text(m - 6, py(0), text="0", fill=t.texto_suave,
                         anchor="e", font=(t.fuente, 8))
        self.create_text(m - 6, py(y_max / 1.15), text=f"{y_max / 1.15:.1f}",
                         fill=t.texto_suave, anchor="e", font=(t.fuente, 8))

        # Línea de magnitud
        if len(datos) > 1:
            puntos = []
            for i, v in enumerate(datos):
                puntos.extend((px(i), py(v)))
            self.create_line(*puntos, fill=t.acento, width=2)
        else:
            self.create_oval(px(0) - 3, py(datos[0]) - 3,
                             px(0) + 3, py(datos[0]) + 3, fill=t.acento, outline="")

class TablaRegistros(tk.Frame):
    """Tabla de registros clasificados con filtro por nivel."""

    FILTROS = ("todos", "alta", "media", "baja")

    def __init__(self, master, tema, al_filtrar, al_elegir_archivo=None):
        super().__init__(master, bg=tema.fondo)
        self.__tema = tema

        barra = tk.Frame(self, bg=tema.fondo)
        barra.pack(fill="x", pady=(0, 6))
        tk.Label(barra, text="Registros", bg=tema.fondo, fg=tema.texto,
                 font=(tema.fuente, 12, "bold")).pack(side="left")
        # Se empaqueta de derecha a izquierda: nivel, y a su izquierda el archivo.
        self.__filtro = ttk.Combobox(barra, values=self.FILTROS, state="readonly",
                                     width=8, style="Tema.TCombobox")
        self.__filtro.set("todos")
        self.__filtro.pack(side="right")
        self.__filtro.bind("<<ComboboxSelected>>", lambda _e: al_filtrar())
        tk.Label(barra, text="Nivel:", bg=tema.fondo,
                 fg=tema.texto_suave, font=(tema.fuente, 10)).pack(side="right", padx=(10, 4))

        self.__filtro_archivo = ttk.Combobox(barra, values=(), state="readonly",
                                             width=30, style="Tema.TCombobox")
        self.__filtro_archivo.pack(side="right")
        if al_elegir_archivo is not None:
            self.__filtro_archivo.bind("<<ComboboxSelected>>",
                                       lambda _e: al_elegir_archivo())
        tk.Label(barra, text="Archivo:", bg=tema.fondo,
                 fg=tema.texto_suave, font=(tema.fuente, 10)).pack(side="right", padx=(10, 4))

        contenedor = tk.Frame(self, bg=tema.fondo)
        contenedor.pack(fill="both", expand=True)
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)

        columnas = ("timestamp", "magnitud", "nivel", "recomendacion")
        self.__arbol = ttk.Treeview(contenedor, columns=columnas, show="headings",
                                    style="Tema.Treeview")
        for col, texto, ancho, minimo in (("timestamp", "Timestamp", 80, 60),
                                          ("magnitud", "Magnitud", 80, 60),
                                          ("nivel", "Nivel", 60, 50),
                                          ("recomendacion", "Recomendación", 520, 300)):
            self.__arbol.heading(col, text=texto)
            self.__arbol.column(col, width=ancho, minwidth=minimo, anchor="w",
                                stretch=(col == "recomendacion"))

        for nivel in ("alta", "media", "baja"):
            self.__arbol.tag_configure(nivel, foreground=tema.color_nivel(nivel))

        scroll_v = ttk.Scrollbar(contenedor, orient="vertical",
                                 command=self.__arbol.yview, style="Tema.Vertical.TScrollbar")
        scroll_h = ttk.Scrollbar(contenedor, orient="horizontal",
                                 command=self.__arbol.xview, style="Tema.Horizontal.TScrollbar")
        self.__arbol.configure(yscrollcommand=scroll_v.set, xscrollcommand=scroll_h.set)
        self.__arbol.grid(row=0, column=0, sticky="nsew")
        scroll_v.grid(row=0, column=1, sticky="ns")
        scroll_h.grid(row=1, column=0, sticky="ew")

    def get_filtro(self):
        return self.__filtro.get()

    def get_archivo(self):
        return self.__filtro_archivo.get()

    def set_archivos(self, nombres):
        self.__filtro_archivo["values"] = list(nombres)

    def set_archivo(self, nombre):
        self.__filtro_archivo.set(nombre)

    def mostrar(self, registros):
        self.__arbol.delete(*self.__arbol.get_children())
        for r in registros:
            self.__arbol.insert("", "end", tags=(r.nivel,), values=(
                f"{r.timestamp:.3f}", f"{r.magnitud:.4f}",
                r.nivel, r.recomendacion.strip()))

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
