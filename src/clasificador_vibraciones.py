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

#Prueba
if __name__=="__main__":
    clasificador = ClasificadorVibraciones(limiteMedio=1.5, limiteAlto=3.0)
    for val in [0.8, 2.1, 4.5]:
        print(f"Magnitud {val}: {clasificador.clasificarMagnitud(val)}")
 
    df = pd.DataFrame({"magnitud": [0.8, 1.5, 2.1, 3.0, 4.5]})
    print(clasificador.clasificar_dataframe(df)[["magnitud", "nivel"]])