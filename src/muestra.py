"""Representa una única muestra de datos leída del sensor (una fila de la
recolección). Guarda los valores de una lectura y sabe calcular su propia
magnitud; no sabe nada de phyphox, csv, ni de cómo se clasifica una vibración.
 
Además ofrece calcular_magnitudes(), que hace el mismo cálculo para
TODAS las filas de un DataFrame a la vez (vectorizado con numpy)."""
 
import math
 
import numpy as np
 
 
class Muestra:
 
    def __init__(self, timestamp, acc_x, acc_y, acc_z):
        self.__timestamp = timestamp
        self.__acc_x = acc_x
        self.__acc_y = acc_y
        self.__acc_z = acc_z
 
    def get_timestamp(self):
        return self.__timestamp
 
    def get_acc_x(self):
        return self.__acc_x
 
    def get_acc_y(self):
        return self.__acc_y
 
    def get_acc_z(self):
        return self.__acc_z
 
    def calcular_magnitud(self):
        """Magnitud de UNA muestra: sqrt(x² + y² + z²)."""
        return math.sqrt(self.__acc_x**2 + self.__acc_y**2 + self.__acc_z**2)
 
    @staticmethod
    def calcular_magnitudes(acc_x, acc_y, acc_z):
        """
        Misma fórmula que calcular_magnitud, pero recibe columnas completas
        (pandas.Series o arrays) y devuelve la magnitud de cada fila.
        """
        return np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
 