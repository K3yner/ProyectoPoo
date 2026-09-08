import os
# aca se importaran las otras clases, creo
class controlador:
    def _init_(self, recolector, csv_manager, clasificador, biblioteca):
        """
        Args:
            recolector: instancia de RecolectorDatos (conexión con phyphox).
            csv_manager: instancia de CSVManager (lectura/escritura de CSV).
            clasificador: instancia de ClasificadorVibraciones.
            biblioteca: instancia de Biblioteca (almacena los resultados).
        """
        self.__recolector = recolector
        self.__csv_manager = csv_manager
        self.__clasificador = clasificador
        self.__biblioteca = biblioteca