import numpy as np
import pandas as pd
 
 
class ClasificadorVibraciones:
    """
    Clase encargada de clasificar la magnitud de vibraciones en nivel baja,
    media y alta, y de ofrecer recomendaciones.
 
    Puede clasificar un solo valor (clasificarMagnitud / muestraClasificacion)
    o un DataFrame completo de una vez (clasificar_dataframe).
    """
 
    RECOMENDACIONES = {
        "baja": "El nivel de la vibración es seguro, se encuentra dentro del rango normal.",
        "media": "El nivel de la vibración es moderado. Se recomienda observar la aparición de grietas.",
        "alta": "Nivel alto de vibración. Riesgo potencial para la estructura.",
    }
 
    def __init__(self, limiteMedio=1.5, limiteAlto=3.0):
        self.__limiteMedio = limiteMedio
        self.__limiteAlto = limiteAlto
 
    def get_limiteMedio(self):
        return self.__limiteMedio
 
    def get_limiteAlto(self):
        return self.__limiteAlto
 
    # ---------------- Un solo valor ----------------
 
    def clasificarMagnitud(self, magnitud):
        if magnitud < self.__limiteMedio:
            return "baja"
        elif magnitud < self.__limiteAlto:
            return "media"
        else:
            return "alta"
 
    def recomendaciones(self, magnitud):
        return self.RECOMENDACIONES[self.clasificarMagnitud(magnitud)]
 
    def muestraClasificacion(self, muestra):
        if isinstance(muestra, (int, float)):
            magnitud = muestra
        elif hasattr(muestra, "calcular_magnitud"):
            magnitud = muestra.calcular_magnitud()
        else:
            raise TypeError("El dato ingresado no es válido, ingrese un número o muestra válida.")
        return {
            "Magnitud": magnitud,
            "Nivel": self.clasificarMagnitud(magnitud),
            "Recomendacion": self.recomendaciones(magnitud),
        }
 
    # ---------------- DataFrame completo ----------------
 
    def clasificar_dataframe(self, df, columna_magnitud="magnitud"):
        """
        Recibe un DataFrame con una columna de magnitudes y devuelve una
        COPIA con dos columnas nuevas: 'nivel' y 'recomendacion'.
        Usa los mismos límites que clasificarMagnitud, pero aplicados a
        todas las filas a la vez (np.select), lo cual es mucho más rápido
        que recorrer fila por fila.
        """
        if columna_magnitud not in df.columns:
            raise KeyError(f"El DataFrame no tiene la columna '{columna_magnitud}'.")
 
        resultado = df.copy()
        mag = resultado[columna_magnitud]
 
        condiciones = [mag < self.__limiteMedio, mag < self.__limiteAlto]
        resultado["nivel"] = np.select(condiciones, ["baja", "media"], default="alta")
        resultado["recomendacion"] = resultado["nivel"].map(self.RECOMENDACIONES)
        return resultado
 
 
if __name__ == "__main__":
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=3.0)
    for val in [0.8, 2.1, 4.5]:
        print(f"Magnitud {val}: {clasificador.clasificarMagnitud(val)}")
 
    df = pd.DataFrame({"magnitud": [0.8, 1.5, 2.1, 3.0, 4.5]})
    print(clasificador.clasificar_dataframe(df)[["magnitud", "nivel"]])