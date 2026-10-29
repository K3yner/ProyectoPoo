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


# ----------------------------------------------------------------------
# Componentes reutilizables
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# Ventana principal
# ----------------------------------------------------------------------
class InterfazVibraciones(tk.Tk):
    """
    Ventana principal.

    Args:
        controlador: instancia de Controlador.
        recolector: instancia de RecolectorDatos (para IP/puerto y estado).
        biblioteca: instancia de Biblioteca (para mostrar los registros).
        clasificador: instancia de ClasificadorVibraciones (umbrales y recomendaciones).
        tema: instancia de Tema (opcional).
        csv_manager: instancia de CSVManager (para listar y cargar los CSV de la carpeta).
    """

    def __init__(self, controlador, recolector, biblioteca, clasificador, tema=None,
                 csv_manager=None):
        super().__init__()
        self.__controlador = controlador
        self.__recolector = recolector
        self.__biblioteca = biblioteca
        self.__clasificador = clasificador
        self.__csv_manager = csv_manager
        self.tema = tema or Tema()
        self.__ocupado = False

        self.title("Monitor de vibraciones")
        self.geometry("1360x880")
        self.minsize(1100, 720)
        self.configure(bg=self.tema.fondo)

        self._configurar_estilos()
        self._construir_encabezado()
        self._construir_conexion()
        self._construir_archivos()
        self._construir_tarjetas()
        self._construir_recomendacion()
        self._construir_panel_central()
        self._construir_log()

        self._refrescar_estado()
        self._refrescar_datos()

        # Al abrir, carga automáticamente el CSV más reciente de la carpeta
        self._actualizar_lista_archivos()
        if self.__combo_archivos.get():
            self._on_cargar_csv()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _configurar_estilos(self):
        t = self.tema
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        for nombre, color in (("Iniciar", t.boton_iniciar),
                              ("Detener", t.boton_detener),
                              ("Neutro", t.boton_neutro)):
            estilo.configure(f"{nombre}.TButton", background=color, foreground=t.boton_texto,
                             font=(t.fuente, 11, "bold"), padding=(18, 10),
                             borderwidth=0, focusthickness=0)
            estilo.map(f"{nombre}.TButton",
                       background=[("disabled", t.boton_desactivado), ("active", color)],
                       foreground=[("disabled", t.texto_suave)])

        estilo.configure("Tema.Treeview", background=t.superficie, fieldbackground=t.superficie,
                         foreground=t.texto, rowheight=24, borderwidth=0,
                         font=(t.fuente, 10))
        estilo.configure("Tema.Treeview.Heading", background=t.superficie_alt,
                         foreground=t.texto, font=(t.fuente, 10, "bold"), borderwidth=0)
        estilo.map("Tema.Treeview", background=[("selected", t.acento)],
                   foreground=[("selected", t.fondo)])
        estilo.map("Tema.Treeview.Heading", background=[("active", t.borde)])

        estilo.configure("Tema.TCombobox", fieldbackground=t.superficie_alt,
                         background=t.superficie_alt, foreground=t.texto,
                         arrowcolor=t.texto, bordercolor=t.borde)
        estilo.configure("Tema.Vertical.TScrollbar", background=t.superficie_alt,
                         troughcolor=t.superficie, arrowcolor=t.texto, bordercolor=t.borde)
        estilo.configure("Tema.Horizontal.TScrollbar", background=t.superficie_alt,
                         troughcolor=t.superficie, arrowcolor=t.texto, bordercolor=t.borde)

    def _construir_encabezado(self):
        t = self.tema
        marco = tk.Frame(self, bg=t.fondo)
        marco.pack(fill="x", padx=20, pady=(16, 6))

        tk.Label(marco, text="Monitor de vibraciones", bg=t.fondo, fg=t.texto,
                 font=(t.fuente, 20, "bold")).pack(side="left")

        estado = tk.Frame(marco, bg=t.fondo)
        estado.pack(side="right")
        self.__punto = tk.Canvas(estado, width=16, height=16, bg=t.fondo,
                                 highlightthickness=0)
        self.__punto.pack(side="left")
        self.__luz = self.__punto.create_oval(2, 2, 14, 14, fill=t.estado_inactivo, outline="")
        self.__lbl_estado = tk.Label(estado, text="Detenido", bg=t.fondo, fg=t.texto_suave,
                                     font=(t.fuente, 11, "bold"))
        self.__lbl_estado.pack(side="left", padx=6)

    def _construir_conexion(self):
        t = self.tema
        marco = tk.Frame(self, bg=t.superficie, highlightbackground=t.borde,
                         highlightthickness=1)
        marco.pack(fill="x", padx=20, pady=6)
        interno = tk.Frame(marco, bg=t.superficie)
        interno.pack(fill="x", padx=14, pady=12)

        def campo(texto, valor, ancho):
            tk.Label(interno, text=texto, bg=t.superficie, fg=t.texto_suave,
                     font=(t.fuente, 10)).pack(side="left", padx=(0, 4))
            entrada = tk.Entry(interno, width=ancho, bg=t.superficie_alt, fg=t.texto,
                               insertbackground=t.texto, relief="flat",
                               font=(t.fuente_mono, 10),
                               highlightbackground=t.borde, highlightthickness=1)
            entrada.insert(0, str(valor))
            entrada.pack(side="left", padx=(0, 14), ipady=3)
            return entrada

        self.__entrada_ip = campo("IP:", self.__recolector.getIP(), 16)
        self.__entrada_puerto = campo("Puerto:", self.__recolector.getPuerto(), 6)

        self.__btn_detener = ttk.Button(interno, text="■  Detener y guardar",
                                        style="Detener.TButton", command=self._on_detener)
        self.__btn_detener.pack(side="right")
        self.__btn_iniciar = ttk.Button(interno, text="▶  Iniciar medición",
                                        style="Iniciar.TButton", command=self._on_iniciar)
        self.__btn_iniciar.pack(side="right", padx=8)

    def _construir_archivos(self):
        t = self.tema
        marco = tk.Frame(self, bg=t.superficie, highlightbackground=t.borde,
                         highlightthickness=1)
        marco.pack(fill="x", padx=20, pady=6)
        interno = tk.Frame(marco, bg=t.superficie)
        interno.pack(fill="x", padx=14, pady=10)

        tk.Label(interno, text="Archivo CSV:", bg=t.superficie, fg=t.texto_suave,
                 font=(t.fuente, 10)).pack(side="left", padx=(0, 6))
        self.__combo_archivos = ttk.Combobox(interno, state="readonly", width=44,
                                             style="Tema.TCombobox")
        self.__combo_archivos.pack(side="left", padx=(0, 10))
        self.__combo_archivos.bind("<<ComboboxSelected>>", lambda _e: self._sincronizar_combo_tabla())
        ttk.Button(interno, text="Cargar", style="Neutro.TButton",
                   command=self._on_cargar_csv).pack(side="left")
        ttk.Button(interno, text="↻  Actualizar lista", style="Neutro.TButton",
                   command=self._actualizar_lista_archivos).pack(side="left", padx=8)
        self.__lbl_archivo = tk.Label(interno, text="Ningún archivo cargado",
                                      bg=t.superficie, fg=t.texto_suave,
                                      font=(t.fuente, 10), anchor="e")
        self.__lbl_archivo.pack(side="right")

    def _construir_tarjetas(self):
        t = self.tema
        marco = tk.Frame(self, bg=t.fondo)
        marco.pack(fill="x", padx=20, pady=6)
        self.__tarjetas = {}
        for i, nivel in enumerate(("baja", "media", "alta")):
            tarjeta = TarjetaNivel(marco, t, nivel)
            tarjeta.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            marco.columnconfigure(i, weight=1, uniform="tarjetas")
            self.__tarjetas[nivel] = tarjeta

    def _construir_recomendacion(self):
        t = self.tema
        self.__marco_reco = tk.Frame(self, bg=t.superficie, highlightbackground=t.borde,
                                     highlightthickness=1)
        self.__marco_reco.pack(fill="x", padx=20, pady=6)
        self.__barra_reco = tk.Frame(self.__marco_reco, bg=t.texto_suave, width=6)
        self.__barra_reco.pack(side="left", fill="y")
        interno = tk.Frame(self.__marco_reco, bg=t.superficie)
        interno.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        self.__lbl_pico = tk.Label(interno, text="Pico máximo: —", bg=t.superficie,
                                   fg=t.texto, font=(t.fuente, 11, "bold"), anchor="w")
        self.__lbl_pico.pack(fill="x")
        self.__lbl_reco = tk.Label(interno, text="Aún no hay mediciones.", bg=t.superficie,
                                   fg=t.texto_suave, font=(t.fuente, 10), anchor="w",
                                   justify="left", wraplength=880)
        self.__lbl_reco.pack(fill="x")

    def _construir_panel_central(self):
        """Gráfica a la izquierda y tabla de registros/recomendaciones a la derecha."""
        t = self.tema
        centro = tk.Frame(self, bg=t.fondo)
        centro.pack(fill="both", expand=True, padx=20, pady=(6, 0))
        centro.rowconfigure(0, weight=1)
        centro.columnconfigure(0, weight=1, uniform="centro")
        centro.columnconfigure(1, weight=1, uniform="centro")

        izquierda = tk.Frame(centro, bg=t.fondo)
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        derecha = tk.Frame(centro, bg=t.fondo)
        derecha.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._construir_grafico(izquierda)
        self._construir_tabla(derecha)

    def _construir_grafico(self, padre):
        t = self.tema
        tk.Label(padre, text="Magnitud en el tiempo", bg=t.fondo, fg=t.texto,
                 font=(t.fuente, 12, "bold")).pack(anchor="w", pady=(0, 6))
        self.__grafico = GraficoMagnitudes(padre, t)
        self.__grafico.pack(fill="both", expand=True)

    def _construir_tabla(self, padre):
        self.__tabla = TablaRegistros(padre, self.tema, self._refrescar_tabla,
                                      self._on_elegir_archivo_tabla)
        self.__tabla.pack(fill="both", expand=True)

    def _construir_log(self):
        self.__log = PanelLog(self, self.tema)
        self.__log.pack(fill="x", padx=20, pady=10)

    # ------------------------------------------------------------------
    # Acciones de los botones
    # ------------------------------------------------------------------
    def _on_iniciar(self):
        if self.__ocupado:
            return
        try:
            puerto = int(self.__entrada_puerto.get())
        except ValueError:
            messagebox.showerror("Puerto inválido", "El puerto debe ser un número entero.")
            return

        self.__recolector.setIP(self.__entrada_ip.get().strip())
        self.__recolector.setPuerto(puerto)

        self.__log.escribir("Conectando con phyphox...")
        self._ejecutar_en_hilo(self.__controlador.iniciar_medicion, self._al_iniciar)

    def _al_iniciar(self, salida, error):
        self._mostrar_salida(salida, error)
        if error is None and self.__recolector.getMidiendo():
            # Cada medición parte de cero: los timestamps de phyphox reinician en 0 y
            # mezclarlos con los de otra medición dibujaría una gráfica sin sentido.
            self.__biblioteca.vaciar()
            self.__lbl_archivo.config(text="Medición en curso...")
            self._refrescar_datos()
            self.__log.escribir("Medición iniciada.")
        elif error is None:
            self.__log.escribir("No se pudo iniciar: revisa la IP/puerto y que el "
                                "acceso remoto de phyphox esté activo.")
            messagebox.showwarning("Sin conexión",
                                   "No se pudo conectar con phyphox.\n"
                                   "Verifica la IP, el puerto y el acceso remoto.")

    def _on_detener(self):
        if self.__ocupado:
            return
        self.__log.escribir("Deteniendo y procesando datos...")
        self._ejecutar_en_hilo(self.__controlador.detener_medicion, self._al_detener)

    def _al_detener(self, salida, error):
        self._mostrar_salida(salida, error)
        if error is None:
            self.__log.escribir("Proceso terminado.")
        self._refrescar_datos()

        nombre = self.__recolector.getNombreArchivo()
        if nombre:
            nombre = nombre.replace("Acelerometro_", "Clasificado_", 1)
        self._actualizar_lista_archivos(seleccionar=nombre)
        if error is None and nombre and self.__biblioteca.obtener_todos():
            self.__lbl_archivo.config(text=f"Mostrando: {nombre}")
        else:
            self.__lbl_archivo.config(text="Ningún archivo cargado")

    # ------------------------------------------------------------------
    # Carga de CSV desde la carpeta de datos
    # ------------------------------------------------------------------
    def _listar_csvs(self):
        """Nombres de los CSV de la carpeta de datos, del más reciente al más antiguo."""
        if self.__csv_manager is None:
            return []
        carpeta = self.__csv_manager.get_direccion_relativa()
        try:
            nombres = [n for n in os.listdir(carpeta) if n.lower().endswith(".csv")]
            nombres.sort(key=lambda n: os.path.getmtime(os.path.join(carpeta, n)),
                         reverse=True)
        except OSError:
            return []
        return nombres

    def _actualizar_lista_archivos(self, seleccionar=None):
        nombres = self._listar_csvs()
        self.__combo_archivos["values"] = nombres
        actual = seleccionar or self.__combo_archivos.get()
        if actual in nombres:
            self.__combo_archivos.set(actual)
        elif nombres:
            clasificados = [n for n in nombres if n.startswith("Clasificado_")]
            self.__combo_archivos.set((clasificados or nombres)[0])
        else:
            self.__combo_archivos.set("")
        self.__tabla.set_archivos(nombres)
        self._sincronizar_combo_tabla()

    def _sincronizar_combo_tabla(self):
        """Mantiene igual el archivo mostrado en ambos selectores."""
        self.__tabla.set_archivo(self.__combo_archivos.get())

    def _on_elegir_archivo_tabla(self):
        """El selector de la tabla carga el archivo apenas se elige."""
        if self.__ocupado:
            self._sincronizar_combo_tabla()  # vuelve al archivo anterior
            return
        self.__combo_archivos.set(self.__tabla.get_archivo())
        self._on_cargar_csv()

    def _on_cargar_csv(self):
        if self.__ocupado:
            return
        nombre = self.__combo_archivos.get()
        if not nombre:
            messagebox.showinfo("Sin archivo", "No hay ningún CSV seleccionado en la carpeta de datos.")
            return
        self.__log.escribir(f"Cargando {nombre}...")
        self._ejecutar_en_hilo(lambda: self._cargar_csv(nombre),
                               lambda salida, error: self._al_cargar_csv(nombre, salida, error))

    def _cargar_csv(self, nombre):
        """Se ejecuta en segundo plano: reemplaza el contenido de la Biblioteca por el CSV."""
        if nombre.startswith("Clasificado_"):
            df = self.__csv_manager.leer(nombre, solo_numericos=False)
            columnas = ["timestamp", "magnitud", "nivel", "recomendacion"]
            if set(columnas) - set(df.columns):
                raise ValueError("el archivo clasificado no tiene las columnas esperadas.")
            df = df.dropna(subset=columnas)
            self.__biblioteca.vaciar()
            cantidad = self.__biblioteca.agregar_dataframe(df)
            print(f"Se cargaron {cantidad} muestras clasificadas.")
        else:
            # CSV crudo de phyphox: se clasifica completo (y se guarda su versión Clasificado_)
            self.__biblioteca.vaciar()
            if self.__controlador.procesar_csv(nombre) is None:
                raise ValueError("el archivo no tiene el formato de una medición de phyphox.")

    def _al_cargar_csv(self, nombre, salida, error):
        self._mostrar_salida(salida, error)
        if error is None:
            self.__lbl_archivo.config(text=f"Mostrando: {nombre}")
        else:
            self.__lbl_archivo.config(text="Ningún archivo cargado")
        self._actualizar_lista_archivos(seleccionar=nombre)
        self._refrescar_datos()

    # ------------------------------------------------------------------
    # Ejecución en segundo plano (las llamadas de red no congelan la ventana)
    # ------------------------------------------------------------------
    def _ejecutar_en_hilo(self, funcion, al_terminar):
        import threading

        self.__ocupado = True
        self._refrescar_estado()
        resultado = queue.Queue()

        def tarea():
            salida = io.StringIO()
            error = None
            try:
                with redirect_stdout(salida):
                    funcion()
            except Exception as e:  # noqa: BLE001
                error = e
            resultado.put((salida.getvalue(), error))

        threading.Thread(target=tarea, daemon=True).start()

        def revisar():
            try:
                salida, error = resultado.get_nowait()
            except queue.Empty:
                self.after(100, revisar)
                return
            self.__ocupado = False
            al_terminar(salida, error)
            self._refrescar_estado()

        self.after(100, revisar)

    def _mostrar_salida(self, salida, error):
        """Pasa al panel de mensajes lo que el Controlador imprimió con print()."""
        if salida.strip():
            self.__log.escribir(salida)
        if error is not None:
            self.__log.escribir(f"Error: {error}")
            messagebox.showerror("Error", str(error))

    # ------------------------------------------------------------------
    # Refresco de la vista
    # ------------------------------------------------------------------
    def _refrescar_estado(self):
        t = self.tema
        midiendo = self.__recolector.getMidiendo()

        if self.__ocupado:
            texto, color = "Procesando...", t.acento
        elif midiendo:
            texto, color = "Midiendo", t.estado_activo
        else:
            texto, color = "Detenido", t.estado_inactivo

        self.__punto.itemconfig(self.__luz, fill=color)
        self.__lbl_estado.config(text=texto, fg=color)

        puede_iniciar = not midiendo and not self.__ocupado
        puede_detener = midiendo and not self.__ocupado
        self.__btn_iniciar.state(["!disabled"] if puede_iniciar else ["disabled"])
        self.__btn_detener.state(["!disabled"] if puede_detener else ["disabled"])

    def _registros_ordenados(self):
        return sorted(self.__biblioteca.obtener_todos(), key=lambda r: r.timestamp)

    def _refrescar_datos(self):
        resumen = self.__controlador.obtener_resumen()
        total = sum(resumen.values())
        for nivel, tarjeta in self.__tarjetas.items():
            tarjeta.actualizar(resumen.get(nivel, 0), total)

        registros = self._registros_ordenados()
        self.__grafico.actualizar([r.magnitud for r in registros],
                                  self.__clasificador.get_limiteMedio(),
                                  self.__clasificador.get_limiteAlto())
        self._refrescar_tabla()
        self._refrescar_recomendacion(registros)

    def _refrescar_tabla(self):
        registros = self._registros_ordenados()
        filtro = self.__tabla.get_filtro()
        if filtro != "todos":
            registros = [r for r in registros if r.nivel == filtro]
        self.__tabla.mostrar(registros)

    def _refrescar_recomendacion(self, registros):
        t = self.tema
        if not registros:
            self.__lbl_pico.config(text="Pico máximo: —")
            self.__lbl_reco.config(text="Aún no hay mediciones.", fg=t.texto_suave)
            self.__barra_reco.config(bg=t.texto_suave)
            return

        pico = max(registros, key=lambda r: r.magnitud)
        self.__lbl_pico.config(text=f"Pico máximo: {pico.magnitud:.4f}  (nivel {pico.nivel})")
        self.__lbl_reco.config(text=pico.recomendacion.strip(), fg=t.texto)
        self.__barra_reco.config(bg=t.color_nivel(pico.nivel))


# ----------------------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------------------
def main():
    from RecolectorDatos import RecolectorDatos
    from csv_manager import CSVManager
    from clasificador_vibraciones import ClasificadorVibraciones
    from biblioteca import Biblioteca
    from Controlador import Controlador

    recolector = RecolectorDatos(
        ip="10.100.8.248",
        variables=["accX", "accY", "accZ", "acc_time"],
        puerto=80,
        direccionRelativa="datos_experimento",
    )
    csv_manager = CSVManager(recolector.getDireccionRelativa())
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=3.0)
    biblioteca = Biblioteca()
    controlador = Controlador(recolector, csv_manager, clasificador, biblioteca)

    # Para cambiar colores:  tema = Tema(); tema.fondo = "#FFFFFF"; ...
    tema = Tema()

    app = InterfazVibraciones(controlador, recolector, biblioteca, clasificador, tema,
                              csv_manager=csv_manager)
    app.mainloop()


if __name__ == "__main__":
    main()