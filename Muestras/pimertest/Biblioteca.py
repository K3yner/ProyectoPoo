"""Clase encargada de almacenar y organizar los registros de vibraciones que
alguien más ya clasificó (ver ClasificadorVibraciones). Biblioteca no sabe
nada sobre umbrales ni cómo se calcula el nivel de una vibración; solo
necesita que cada registro tenga un atributo `nivel` con valor
alta, media o baja"""

class Biblioteca:

    NIVELES_VALIDOS = ("alta", "media", "baja")
 
    def __init__(self):
        
        self.__registros = {nivel: [] for nivel in self.NIVELES_VALIDOS}
 
    def agregar(self, registro):
        
        nivel = registro.nivel
        if nivel not in self.NIVELES_VALIDOS:
            raise ValueError(f"Nivel desconocido: {nivel}")
        self.__registros[nivel].append(registro)
 
    def obtener_por_nivel(self, nivel):
        """Devuelve todos los registros guardados para un nivel dado."""
        return self.__registros.get(nivel, [])
 
    def obtener_todos(self):

        return [registro for lista in self.__registros.values() for registro in lista]
 
    def contar_por_nivel(self):
       
        return {nivel: len(lista) for nivel, lista in self.__registros.items()}
 

