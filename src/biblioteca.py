"""Clase encargada de almacenar y organizar los registros de vibraciones que
alguien más ya clasificó (ver ClasificadorVibraciones). Biblioteca no sabe
nada sobre umbrales ni cómo se calcula el nivel de una vibración; solo
necesita que cada registro tenga un atributo `nivel` con valor
alta, media o baja.
 
Ahora también puede recibir un DataFrame clasificado completo
(agregar_dataframe) y devolver sus registros como DataFrame (a_dataframe)."""
 
import pandas as pd
 
from registro_clasificado import RegistroClasificado
 
 
class Biblioteca:
 
    NIVELES_VALIDOS = ("alta", "media", "baja")
 
    def __init__(self):
        self.__registros = {nivel: [] for nivel in self.NIVELES_VALIDOS}
 
    def agregar(self, registro):
        nivel = registro.nivel
        if nivel not in self.NIVELES_VALIDOS:
            raise ValueError(f"Nivel desconocido: {nivel}")
        self.__registros[nivel].append(registro)
 
    def agregar_dataframe(self, df):
        """
        Convierte cada fila de un DataFrame clasificado en un
        RegistroClasificado y lo agrega. El DataFrame debe tener las
        columnas: timestamp, magnitud, nivel, recomendacion.
        Devuelve cuántos registros se agregaron.
        """
        requeridas = {"timestamp", "magnitud", "nivel", "recomendacion"}
        faltantes = requeridas - set(df.columns)
        if faltantes:
            raise KeyError(f"Faltan columnas en el DataFrame: {faltantes}")
 
        for fila in df.itertuples(index=False):
            self.agregar(RegistroClasificado(
                timestamp=fila.timestamp,
                magnitud=fila.magnitud,
                nivel=fila.nivel,
                recomendacion=fila.recomendacion,
            ))
        return len(df)
 
    def obtener_por_nivel(self, nivel):
        return self.__registros.get(nivel, [])
 
    def obtener_todos(self):
        return [registro for lista in self.__registros.values() for registro in lista]
 
    def contar_por_nivel(self):
        return {nivel: len(lista) for nivel, lista in self.__registros.items()}
 
    def a_dataframe(self, nivel=None):
        """Devuelve los registros (todos o de un nivel) como DataFrame ordenado por tiempo."""
        registros = self.obtener_por_nivel(nivel) if nivel else self.obtener_todos()
        df = pd.DataFrame(
            [(r.timestamp, r.magnitud, r.nivel, r.recomendacion) for r in registros],
            columns=["timestamp", "magnitud", "nivel", "recomendacion"],
        )
        return df.sort_values("timestamp").reset_index(drop=True)
 
    def vaciar(self):
        self.__registros = {nivel: [] for nivel in self.NIVELES_VALIDOS}
 