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
        
        self.__recolector.iniciar()

    def detener_medicion(self):
      
        self.__recolector.detener()
        nombre_archivo = self.__recolector.getNombreArchivo()
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
    from recolector_datos import RecolectorDatos
    from csv_manager import CSVManager
    from clasificador_vibraciones import ClasificadorVibraciones
    from Biblioteca import Biblioteca

    recolector = RecolectorDatos(
        ip="192.168.1.29",
        variables=["accX", "accY", "accZ", "acc_time"],
    )
    csv_manager = CSVManager("datos_experimentos")
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=3.0)
    biblioteca = Biblioteca()

    controlador = Controlador(recolector, csv_manager, clasificador, biblioteca)
    controlador.menu()