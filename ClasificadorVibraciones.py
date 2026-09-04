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
        """
        Recibe valores de magnitud y los clasifica según los límites
        """
        if magnitud<self.__limiteMedio:
            return "baja"
        elif magnitud<self.__limiteAlto:
            return "media"
        else:
            return "alta"

    def recomendaciones(self, magnitud):
        """
        Devuelve recomendiaciones basadas en los niveles de riesgo
        """
        nivel=self.clasificarMagnitud(magnitud)
        if nivel=="baja":
            return "El nivel de la vibración es segura, se encuentran dentro del rango normal."
        elif nivel== "media":
            return "El nivel de la vibración es moderada, Se recomienda observar la aparición de grietas. "
        else:
            return "Nivel alto de vibración. Riesgo potencial para la estructura."

    def muestraClasificacion(self, muestra):
        """
        Recibe una muestra, extrae la magnitud y devuelve la clasificación y recomendación
        """
        if isinstance(muestra,(int, float)):
            magnitud=muestra
        elif hasattr(muestra, "calcular magnitud"):
            magnitud=muestra.calcularMagnitud()
        else:
            raise TypeError("El dato ingresado no es válido, ingrese un número o muestra válida.")

        nivel=self.clasificarMagnitud(magnitud)
        reco=self.recomendaciones(magnitud)
        return{
            "Magnitud":magnitud,
            "Nivel":nivel,
            "Recomendacion:":reco
        }

    


#Prueba
if __name__=="__main__":
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=3.0)
    print("-----Prueba-----")
    print("Prueba, valor 0.8", clasificador.clasificarMagnitud(0.08))
    print("Prueba, valor 2.1", clasificador.clasificarMagnitud(2.1))
    print("Prueba, valor 4.5", clasificador.clasificarMagnitud(4.5))
    for val in [0.8, 2.1, 4.5]:
        nivel=clasificador.clasificarMagnitud(val)
        reco=clasificador.recomendaciones(val)
        print(f"Magnitud {val}, {nivel}: {reco}")

    resultado=clasificador.muestraClasificacion(2.5)
    print("Resultado:", resultado)