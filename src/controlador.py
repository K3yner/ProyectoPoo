
"""
controlador.py
 
Clase orquestadora del programa: conecta RecolectorDatos, CSVManager,
ClasificadorVibraciones y Biblioteca. No sabe nada de interfaces gráficas;
solo expone métodos simples (iniciar, detener, resumen) que cualquier
interfaz (botones, consola, etc.) puede llamar.
 
Flujo completo al detener una medición:
    phyphox --(buffer completo)--> DataFrame crudo --> CSV crudo
    CSV crudo --> DataFrame --> + magnitud --> + nivel/recomendación
             --> CSV clasificado  y  Biblioteca
"""
 
from muestra import Muestra
 
 
class Controlador:
 
    # Nombre de la columna de phyphox  ->  nombre interno del programa.
    # Gracias a esto el orden de las columnas en el CSV ya no importa.
    COLUMNAS = {
        "acc_time": "timestamp",
        "accX": "acc_x",
        "accY": "acc_y",
        "accZ": "acc_z",
    }
 
    def __init__(self, recolector, csv_manager, clasificador, biblioteca):
        self.__recolector = recolector
        self.__csv_manager = csv_manager
        self.__clasificador = clasificador
        self.__biblioteca = biblioteca
        self.__ultimo_resultado = None  # DataFrame clasificado de la última medición
 
    def get_ultimo_resultado(self):
        return self.__ultimo_resultado
 
    # ------------------------------------------------------------------ #
    # Medición
    # ------------------------------------------------------------------ #
 
    def iniciar_medicion(self):
        if self.__recolector._iniciar_medicion() is None:
            print("No se pudo conectar con phyphox. Revisa la IP, el puerto y que el acceso remoto esté activo.")
        else:
            print("Medición iniciada. Elige 'Detener medición' cuando termines.")
 
    def detener_medicion(self):
        self.__recolector._detener_medicion()
 
        # Descarga TODO lo que phyphox registró entre start y stop
        if not self.__recolector._descargar_datos():
            print("No se generó ningún archivo de medición: no hay datos capturados.")
            return None
 
        ruta_csv = self.__recolector._guardar_csv()
        if ruta_csv is None:
            print("No se generó ningún archivo de medición.")
            return None
 
        print(f"Datos crudos guardados en: {ruta_csv}")
        return self.procesar_csv(self.__recolector.getNombreArchivo())
 
    # ------------------------------------------------------------------ #
    # Procesamiento con DataFrames
    # ------------------------------------------------------------------ #
 
    def procesar_csv(self, nombre_archivo):
        """Lee un CSV de mediciones, lo clasifica completo y lo guarda."""
        df = self.__csv_manager.leer(nombre_archivo)
        resultado = self.procesar_dataframe(df)
        if resultado is None:
            return None
 
        nombre_clasificado = nombre_archivo.replace("Acelerometro_", "Clasificado_", 1)
        if nombre_clasificado == nombre_archivo:
            nombre_clasificado = "Clasificado_" + nombre_archivo
        ruta = self.__csv_manager.guardar(resultado, nombre_clasificado)
        print(f"Resultados clasificados guardados en: {ruta}")
        return resultado
 
    def procesar_dataframe(self, df):
        """
        Recibe el DataFrame crudo (columnas de phyphox) y:
          1. Renombra columnas a nombres internos (por nombre, no por posición).
          2. Calcula la magnitud de todas las filas a la vez.
          3. Clasifica todas las filas a la vez.
          4. Guarda cada fila clasificada en la Biblioteca.
        Devuelve el DataFrame clasificado.
        """
        faltantes = set(self.COLUMNAS) - set(df.columns)
        if faltantes:
            print(f"El archivo no tiene las columnas necesarias: {faltantes}")
            return None
        if df.empty:
            print("El archivo no contiene filas válidas.")
            return None
 
        df = df.rename(columns=self.COLUMNAS)[list(self.COLUMNAS.values())]
        df = df.sort_values("timestamp").reset_index(drop=True)
 
        df["magnitud"] = Muestra.calcular_magnitudes(df["acc_x"], df["acc_y"], df["acc_z"])
        clasificado = self.__clasificador.clasificar_dataframe(df, columna_magnitud="magnitud")
 
        cantidad = self.__biblioteca.agregar_dataframe(clasificado)
        print(f"Se clasificaron {cantidad} muestras.")
 
        self.__ultimo_resultado = clasificado
        return clasificado
 
    # ------------------------------------------------------------------ #
    # Consultas
    # ------------------------------------------------------------------ #
 
    def obtener_resumen(self):
        return self.__biblioteca.contar_por_nivel()
 
    def mostrar_resumen(self):
        conteo = self.obtener_resumen()
        total = sum(conteo.values())
        if total == 0:
            print("Todavía no hay muestras clasificadas.")
            return
 
        print(f"\nTotal de muestras clasificadas: {total}")
        for nivel in ("baja", "media", "alta"):
            porcentaje = 100 * conteo[nivel] / total
            print(f"  {nivel:<6}: {conteo[nivel]:>6}  ({porcentaje:5.1f} %)")
 
        df = self.__biblioteca.a_dataframe()
        print("\nEstadísticas de magnitud por nivel:")
        print(df.groupby("nivel")["magnitud"].agg(["count", "min", "mean", "max"]).round(3))
 
        pico = df.loc[df["magnitud"].idxmax()]
        print(f"\nPico máximo: {pico['magnitud']:.3f} en t = {pico['timestamp']:.3f} s ({pico['nivel']})")
        print(f"Recomendación: {pico['recomendacion']}")
 
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
                self.mostrar_resumen()
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
        ip="10.100.1.155",
        variables=["accX", "accY", "accZ", "acc_time"],
        puerto=80,
        direccionRelativa="datos_experimento",
    )
    csv_manager = CSVManager(recolector.getDireccionRelativa())
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=3.0)
    biblioteca = Biblioteca()
 
    controlador = Controlador(recolector, csv_manager, clasificador, biblioteca)
    controlador.menu()