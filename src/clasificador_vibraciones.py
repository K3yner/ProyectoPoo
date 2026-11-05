import numpy as np
import pandas as pd

from muestra import Muestra


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
        nivel=self.clasificarMagnitud(magnitud)
        reco=self.recomendaciones(magnitud)
        return{
            "Magnitud":magnitud,
            "Nivel":nivel,
            "Recomendacion":reco
        }

    # ---------------- DataFrame completo ----------------

    def clasificar_dataframe(self, df):
        """
        Clasifica todas las filas de un DataFrame de una vez.

        Si el DataFrame ya tiene una columna `magnitud`, la usa. Si no, la
        calcula a partir de accX, accY y accZ. Devuelve una copia con las
        columnas `magnitud`, `nivel` y `recomendacion` agregadas.
        """
        resultado = df.copy()
        if "magnitud" not in resultado.columns:
            faltantes = [c for c in ("accX", "accY", "accZ") if c not in resultado.columns]
            if faltantes:
                raise KeyError(f"Faltan columnas para calcular la magnitud: {faltantes}")
            resultado["magnitud"] = Muestra.calcular_magnitudes(
                resultado["accX"], resultado["accY"], resultado["accZ"])

        # Mismos límites que clasificarMagnitud: < medio -> baja, < alto -> media, resto -> alta
        magnitud = resultado["magnitud"]
        resultado["nivel"] = np.select(
            [magnitud < self.__limiteMedio, magnitud < self.__limiteAlto],
            ["baja", "media"],
            default="alta",
        )
        resultado["recomendacion"] = resultado["nivel"].map(self.RECOMENDACIONES)
        return resultado

#Prueba
if __name__=="__main__":
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=3.0)
    for val in [0.8, 2.1, 4.5]:
        print(f"Magnitud {val}: {clasificador.clasificarMagnitud(val)}")
 
    df = pd.DataFrame({"magnitud": [0.8, 1.5, 2.1, 3.0, 4.5]})
    print(clasificador.clasificar_dataframe(df)[["magnitud", "nivel"]])