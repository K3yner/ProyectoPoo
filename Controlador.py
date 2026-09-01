
class controlador:
    def __init__(self, ventana_principal):
        """
        constructor de la clase controlador.
        Inicializa la ventada de la interfaz gráfica y configurs todos sus botonoes"""

        self.ventana = ventana_principal
        self.vantana.title("Sistema de Medición de Vibraciones") 
        self.ventana.geometry("500x400")

        self.ruta_archivo = None
    