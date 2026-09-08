
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

    def iniciar_medicion(self):
        """Le pide al recolector que empiece a tomar datos de phyphox."""
        self.__recolector.iniciar()

    def detener_medicion(self):
        """
        Detiene la recolección de phyphox (lo que guarda el CSV crudo) y
        dispara el procesamiento completo de ese archivo.
        """
        self.__recolector.detener()
        nombre_archivo = self.__recolector.getNombreArchivo()
        self._procesar_csv(nombre_archivo)

    def _procesar_csv(self, nombre_archivo):
        """
        Lee un CSV ya guardado, reconstruye cada fila como Muestra, la
        clasifica y guarda el resultado en la biblioteca.
        """
        filas = self._csv_manager.leer(nombre_archivo)

        for fila in filas:
            timestamp, acc_x, acc_y, acc_z = fila
            muestra = Muestra(float(timestamp), float(acc_x), float(acc_y), float(acc_z))

            resultado = self.__clasificador.muestraClasificacion(muestra)

            registro = RegistroClasificado(
                timestamp=muestra.get_timestamp(),
                magnitud=resultado["Magnitud"],
                nivel=resultado["Nivel"],
                recomendacion=resultado["Recomendacion"]
            )

            self.__biblioteca.agregar(registro)

    def obtener_resumen(self):
        """Devuelve cuántos registros hay guardados por cada nivel de vibración."""
        return self.__biblioteca.contar_por_nivel()