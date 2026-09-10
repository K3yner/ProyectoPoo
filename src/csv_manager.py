"""
csv_manager.py

Clase encargada de la persistencia de datos del experimento en archivos CSV.
Su única responsabilidad es escribir y leer datos; no sabe nada sobre cómo
se obtuvieron esos datos (phyphox, un sensor simulado, etc.), lo que permite
reutilizarla para guardar mediciones crudas, datos filtrados o picos detectados.
"""

import os
import csv


class CSVManager:
    

    def __init__(self, direccion_relativa="datos_experimento"):
        
        self.__direccion_relativa = direccion_relativa
        if not os.path.exists(self.__direccion_relativa):
            os.makedirs(self.__direccion_relativa)

    # Métodos

    def get_direccion_relativa(self):
        
        return self.__direccion_relativa

    def set_direccion_relativa(self, direccion_relativa):
        """Cambia la carpeta donde se guardan los archivos (la crea si no existe)."""
        self.__direccion_relativa = direccion_relativa
        if not os.path.exists(self.__direccion_relativa):
            os.makedirs(self.__direccion_relativa)

    def guardar(self, datos, encabezados, nombre_archivo):
        
        if not datos:
            print("CSVManager: no hay datos para guardar.")  # cambiar por logging en la versión final
            return None

        ruta_completa = os.path.join(self.__direccion_relativa, nombre_archivo)
        with open(ruta_completa, mode="w", newline="", encoding="utf-8") as archivo_csv:
            escritor = csv.writer(archivo_csv)
            escritor.writerow(encabezados)
            escritor.writerows(datos)

        return ruta_completa

    def leer(self, nombre_archivo):
        
        ruta_completa = os.path.join(self.__direccion_relativa, nombre_archivo)
        with open(ruta_completa, mode="r", newline="", encoding="utf-8") as archivo_csv:
            lector = csv.reader(archivo_csv)
            encabezados = next(lector)
            datos = [fila for fila in lector]

        return encabezados, datos

    @staticmethod
    def generar_nombre_archivo(prefijo, fecha_hora):

        fecha_str = fecha_hora.strftime("%Y-%m-%d")
        hora_str = fecha_hora.strftime("%H-%M-%S")
        return f"{prefijo}_{fecha_str}_{hora_str}.csv"