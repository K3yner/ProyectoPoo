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

#Prueba
if __name__=="__main__":
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=.0)
    print("-----Prueba-----")
    print("Prueba, valor 0.8", clasificador.clasificarMagnitud(0.08))
    print("Prueba, valor 2.1", clasificador.clasificarMagnitud(2.1))
    print("Prueba, valor 4.5", clasificador.clasificarMagnitud(4.5))

        