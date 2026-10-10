import numpy as np
import pandas as pd


class ClasificadorVibraciones:
    """
    Clase encargada de clasificar la magnitud de vibraciones en nivel baja, media y alta, y de ofrecer recomendaciones
    """
    def __init__(self, limiteMedio=1.5, limiteAlto=3.0):
        #Límites de clasificación de magnitudes
        self.__limiteMedio=limiteMedio
        self.__limiteAlto=limiteAlto

    def get_limiteMedio(self):
        return self.__limiteMedio

    def get_limiteAlto(self):
        return self.__limiteAlto

    def clasificarMagnitud(self, magnitud):
        
        if magnitud<self.__limiteMedio:
            return "baja"
        elif magnitud<self.__limiteAlto:
            return "media"
        else:
            return "alta"

    def recomendaciones(self, magnitud):
        
        nivel=self.clasificarMagnitud(magnitud)
        if nivel=="baja":
            return "El nivel de la vibración es segura, se encuentran dentro del rango normal."
        elif nivel== "media":
            return "El nivel de la vibración es moderada, Se recomienda observar la aparición de grietas. "
        else:
            return "Nivel alto de vibración. Riesgo potencial para la estructura."

    def muestraClasificacion(self, muestra):
       
        if isinstance(muestra,(int, float)):
            magnitud=muestra
        elif hasattr(muestra, "calcular_magnitud"):
            magnitud=muestra.calcular_magnitud()
        else:
            raise TypeError("El dato ingresado no es válido, ingrese un número o muestra válida.")
        nivel=self.clasificarMagnitud(magnitud)
        reco=self.recomendaciones(magnitud)
        return{
            "Magnitud":magnitud,
            "Nivel":nivel,
            "Recomendacion":reco
        }

    def clasificarDataFrame(self, df):
        if "magnitud" not in df.columns:
            raise KeyError("El DataFrame debe contener la columna de magnitud para poder clasificarse.")

        condiciones = [
            df["magnitud"] < self.get_limiteMedio(),
            (df["magnitud"] >= self.get_limiteMedio()) & (df["magnitud"] < self.get_limiteAlto()),
            df["magnitud"] >= self.get_limiteAlto()
        ]

        opcionesNivel = ["bajo", "media", "alta"]

        opciones_rec = [
            "El nivel de la vibración es segura, se encuentra dentro del rango normal.",
            "El nivel de la vibración es moderada. Se recomienda observar la aparición de grietas.",
            "El nivel de vibración es alto. Riesgo potencial para la estructura."
        ]

        df["nivel"] = np.select(condiciones, opcionesNivel, default="desconocido")
        df["recomendacion"] = np.select(condiciones, opciones_rec, default="sin recomendación.")
        return df


#Prueba
if __name__=="__main__":
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=3.0)
    print("-----Prueba-----")
    print("Prueba, valor 0.08", clasificador.clasificarMagnitud(0.08))
    print("Prueba, valor 2.1", clasificador.clasificarMagnitud(2.1))
    print("Prueba, valor 4.5", clasificador.clasificarMagnitud(4.5))
    for val in [0.8, 2.1, 4.5]:
        nivel=clasificador.clasificarMagnitud(val)
        reco=clasificador.recomendaciones(val)
        print(f"Magnitud {val}, {nivel}: {reco}")
    resultado=clasificador.muestraClasificacion(2.5)
    print("Resultado:", resultado)