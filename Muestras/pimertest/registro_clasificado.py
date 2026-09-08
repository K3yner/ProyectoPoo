class RegistroClasificado:
    """
    Representa una muestra ya clasificada: une el timestamp, la magnitud,
    el nivel de vibración ("alta", "media" o "baja") y la recomendación
    asociada, para poder guardarse en la Biblioteca.
    """

    def __init__(self, timestamp, magnitud, nivel, recomendacion):
        self.__timestamp = timestamp
        self.__magnitud = magnitud
        self.__nivel = nivel
        self.__recomendacion = recomendacion

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def magnitud(self):
        return self.__magnitud

    @property
    def nivel(self):
        return self.__nivel

    @property
    def recomendacion(self):
        return self.__recomendacion