import os
# aca se importaran las otras clases, creo
class controlador:
    def __init__(self, ventana_principal):
        """
        constructor de la clase controlador.
        Inicializa la ventada de la interfaz gráfica y configurs todos sus botonoes"""

        self.ventana = ventana_principal
        self.vantana.title("Sistema de Medición de Vibraciones") 
        self.ventana.geometry("500x400")
        self.ruta_archivo = None
        #atributo que guarda la ruta del archivo

        # --- Componentes de la Interfaz --- 

        self.label.titulo = tk.Label(
            self.ventana,
            text="Medidor de Vibraciones Vehiculares",
            font=("Arial", 16, "bold")
        )
        self.label_titulo.pack(pady=15)
        #boton de interaccion 
        self.boton_cargar = tk.boton(
            self.ventana, 
            text="1. Cargar Archivo",
        )