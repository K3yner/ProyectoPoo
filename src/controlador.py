"""
controlador.py

Clase orquestadora del programa: conecta RecolectorDatos, CSVManager,
ClasificadorVibraciones y Biblioteca. No sabe nada de interfaces gráficas
ni de consola -- solo expone métodos simples (iniciar, detener) que
cualquier interfaz (botones, consola, etc.) puede llamar.
"""

from muestra import Muestra
from registro_clasificado import RegistroClasificado


class Controlador:
  

    def __init__(self, recolector, csv_manager, clasificador, biblioteca):
        
        self.__recolector = recolector
        self.__csv_manager = csv_manager
        self.__clasificador = clasificador
        self.__biblioteca = biblioteca

    def iniciar_medicion(self):
        
        self.__recolector._iniciar_medicion()

    def detener_medicion(self):
        self.__recolector._detener_medicion()

        if not self.__recolector.getDatos():
            datos_json = self.__recolector._obtener_datos()
            if datos_json is not None:
                self.__recolector._procesar_datos_json(datos_json)

        if not self.__recolector.getDatos():
            print("No se generó ningún archivo de medición: no hay datos capturados.")
            return

        ruta_csv = self.__recolector._guardar_csv()
        if ruta_csv is None:
            print("No se generó ningún archivo de medición.")
            return

        nombre_archivo = self.__recolector.getNombreArchivo()
        if nombre_archivo is None:
            print("No se generó ningún archivo de medición.")
            return

        self._procesar_csv(nombre_archivo)

    def _procesar_csv(self, nombre_archivo):
        
        _, filas = self.__csv_manager.leer(nombre_archivo)

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
        
        return self.__biblioteca.contar_por_nivel()

    def menu(self):
        
        while True:
            print("\n--- Monitor de vibraciones ---")
            print("1. Iniciar medición")
            print("2. Detener medición")
            print("3. Ver resumen")
            print("4. Salir")
            opcion = input("Elige una opción: ")

            if opcion == "1":
                self.iniciar_medicion()
            elif opcion == "2":
                self.detener_medicion()
            elif opcion == "3":
                print(self.obtener_resumen())
            elif opcion == "4":
                print("Saliendo...")
                break
            else:
                print("Opción no válida.")


if __name__ == "__main__":
    from RecolectorDatos import RecolectorDatos
    from csv_manager import CSVManager
    from clasificador_vibraciones import ClasificadorVibraciones
    from biblioteca import Biblioteca

    recolector = RecolectorDatos(
        ip="10.100.8.248",
        variables=["accX", "accY", "accZ", "acc_time"],
        puerto=80,
        direccionRelativa="datos_experimento"
    )
    csv_manager = CSVManager(recolector.getDireccionRelativa())
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=3.0)
    biblioteca = Biblioteca()

    controlador = Controlador(recolector, csv_manager, clasificador, biblioteca)
    controlador.menu()