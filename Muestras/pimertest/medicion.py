"""Representa una única muestra de datos leída del sensor (una fila de la
recolección). Es un objeto simple que solo guarda los valores de una
lectura y sabe calcular su propia magnitud; no sabe nada de phyphox,
csv, ni de cómo se clasifica una vibración"""

 
import math
 
 
class Muestra:
    
 
    def __init__(self, timestamp, acc_x, acc_y, acc_z):
        
        self.__timestamp = timestamp
        self.__acc_x = acc_x
        self.__acc_y = acc_y
        self.__acc_z = acc_z
 
    # Métodos
 
    def get_timestamp(self):
        
        return self.__timestamp
 
    def get_acc_x(self):
        
        return self.__acc_x
 
    def get_acc_y(self):
        
        return self.__acc_y
 
    def get_acc_z(self):
        
        return self.__acc_z
 
    def calcular_magnitud(self):
       
 

        return math.sqrt(self.__acc_x**2 + self.__acc_y**2 + self.__acc_z**2)