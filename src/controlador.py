"""
controlador.py

Clase orquestadora del programa: conecta RecolectorDatos, CSVManager,
ClasificadorVibraciones y Biblioteca. No sabe nada de interfaces gráficas
ni de consola -- solo expone métodos simples (iniciar, detener) que
cualquier interfaz (botones, consola, etc.) puede llamar.
"""

import os

import pandas as pd


class Controlador:
  

    def __init__(self, recolector, csv_manager, clasificador, biblioteca):
        
        self.__recolector = recolector
        self.__csv_manager = csv_manager
        self.__clasificador = clasificador
        self.__biblioteca = biblioteca
        self.__ultimo_tiempo = None  # último acc_time recibido en vivo

    def iniciar_medicion(self):
        self.__ultimo_tiempo = None
        self.__recolector._iniciar_medicion()

    def detener_medicion(self):
        self.__recolector._detener_medicion()

        if not self.__recolector.getDatos():
            datos_json = self.__recolector._obtener_datos(completo=True)
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

        # Lo mostrado en vivo se reemplaza por la medición completa guardada
        self.__biblioteca.vaciar()
        self._procesar_csv(nombre_archivo)

    # ---------------- Medición en vivo ----------------

    def obtener_muestras_nuevas(self):
        """Pide a phyphox las muestras que llegaron desde la última consulta y
        las devuelve clasificadas en un DataFrame (sin tocar la Biblioteca).
        Devuelve None si no hubo conexión."""
        datos_json = self.__recolector._obtener_datos_nuevos(self.__ultimo_tiempo)
        if datos_json is None:
            return None
        df = self._json_a_dataframe(datos_json)
        if df.empty:
            return df
        self.__ultimo_tiempo = float(df["acc_time"].iloc[-1])
        return self._clasificar(df)

    def agregar_registros(self, df_clasificado):
        """Agrega a la Biblioteca un DataFrame ya clasificado."""
        self.__biblioteca.agregar_dataframe(df_clasificado)

    def _json_a_dataframe(self, datos_json):
        buffers = datos_json.get("buffer", {})
        columnas = {var: (buffers.get(var, {}).get("buffer") or [])
                    for var in self.__recolector.getVariables()}
        n = min((len(valores) for valores in columnas.values()), default=0)
        df = pd.DataFrame({var: valores[:n] for var, valores in columnas.items()})
        return df.apply(pd.to_numeric, errors="coerce").dropna().reset_index(drop=True)

    def _clasificar(self, df):
        """Clasifica un DataFrame crudo (accX, accY, accZ, acc_time) y lo deja
        con las columnas de los archivos Clasificado_."""
        clasificado = self.__clasificador.clasificar_dataframe(df)
        return pd.DataFrame({
            "timestamp": clasificado["acc_time"],
            "acc_x": clasificado["accX"],
            "acc_y": clasificado["accY"],
            "acc_z": clasificado["accZ"],
            "magnitud": clasificado["magnitud"],
            "nivel": clasificado["nivel"],
            "recomendacion": clasificado["recomendacion"],
        })

    def _procesar_csv(self, nombre_archivo):
        """Lee un CSV crudo de la carpeta, lo clasifica, carga los registros en la
        Biblioteca y guarda su versión Clasificado_ en la carpeta de datos.

        CSVManager.leer() devuelve un DataFrame con las columnas identificadas
        por nombre (el recolector guarda accX, accY, accZ, acc_time).
        Devuelve el DataFrame clasificado, o None si el archivo no tiene datos."""
        df = self.__csv_manager.leer(nombre_archivo)

        requeridas = ("acc_time", "accX", "accY", "accZ")
        faltantes = [col for col in requeridas if col not in df.columns]
        if faltantes:
            raise ValueError(f"faltan las columnas {faltantes}")
        if df.empty:
            print(f"{nombre_archivo} no tiene muestras válidas.")
            return None

        clasificado = self._clasificar(df)

        self.__biblioteca.agregar_dataframe(clasificado)

        nombre_base = os.path.basename(nombre_archivo)
        nombre_clasificado = nombre_base.replace("Acelerometro_", "Clasificado_", 1)
        if nombre_clasificado == nombre_base:
            nombre_clasificado = f"Clasificado_{nombre_base}"
        ruta = self.__csv_manager.guardar(clasificado, nombre_clasificado)
        if ruta:
            print(f"Se clasificaron {len(clasificado)} muestras y se guardaron en {nombre_clasificado}.")
        return clasificado

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