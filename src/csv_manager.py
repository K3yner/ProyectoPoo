"""""
csv_manager.py
 
Clase encargada de la persistencia de datos del experimento en archivos CSV.
Su única responsabilidad es escribir y leer datos; no sabe nada sobre cómo
se obtuvieron (phyphox, un sensor simulado, etc.).
 
Trabaja con pandas.DataFrame, de modo que al leer un archivo las columnas
quedan identificadas por su nombre y con tipos numéricos correctos.
"""
 
import os
 
import pandas as pd
 
 
class CSVManager:
 
    def __init__(self, direccion_relativa="datos_experimento"):
        self.__direccion_relativa = direccion_relativa
        os.makedirs(self.__direccion_relativa, exist_ok=True)
 
    def get_direccion_relativa(self):
        return self.__direccion_relativa
 
    def set_direccion_relativa(self, direccion_relativa):
        """Cambia la carpeta donde se guardan los archivos (la crea si no existe)."""
        self.__direccion_relativa = direccion_relativa
        os.makedirs(self.__direccion_relativa, exist_ok=True)
 
    def guardar(self, df, nombre_archivo):
        """Guarda un DataFrame como CSV. Devuelve la ruta o None si está vacío."""
        if df is None or df.empty:
            print("CSVManager: no hay datos para guardar.")
            return None
 
        ruta_completa = os.path.join(self.__direccion_relativa, nombre_archivo)
        df.to_csv(ruta_completa, index=False, encoding="utf-8")
        return ruta_completa
 
    def leer(self, nombre_archivo, solo_numericos=True):
        """
        Lee un CSV y devuelve un DataFrame.
 
        Con solo_numericos=True (mediciones crudas) todas las columnas se
        convierten a número y se descartan filas incompletas o corruptas.
        Con False se lee tal cual (útil para CSV ya clasificados con texto).
        """
        ruta_completa = os.path.join(self.__direccion_relativa, nombre_archivo)
        df = pd.read_csv(ruta_completa, encoding="utf-8")
        if solo_numericos:
            df = df.apply(pd.to_numeric, errors="coerce").dropna().reset_index(drop=True)
        return df
 
    @staticmethod
    def generar_nombre_archivo(prefijo, fecha_hora):
        fecha_str = fecha_hora.strftime("%Y-%m-%d")
        hora_str = fecha_hora.strftime("%H-%M-%S")
        return f"{prefijo}_{fecha_str}_{hora_str}.csv"