import os
import csv
import time
from datetime import datetime
import requests

class RecolectorDatos:
    """
    Clase encargda de recolectar los datos del phyphox a través de la 
    función acceso remoto.

    Necesita los paquetes:
        - os
        - csv
        - time
        - datetime
        - requests

    si no se tiene alguno de estos basta con ejecutar el comando:

        pip install {nombre paquete}
    
    para instalarlo.

    """

    def __init__(self, ip, variables, puerto= 80, direccionRelativa= "datos_experimento", intervaloMuestreo= 0.1):
        """
        Inicializa la clase RecolectorDatos.

        Args:
            ip (str): Dirección IP del dispositivo phyphox.
            variables (list): Lista de variables a recolectar. Para el acelerómetro son accX, accY, accZ, acc_time
            puerto (int, optional): Puerto de acceso remoto. Por defecto es 8080, ya que es el que suele utilizar phyphox
            direccionRelativa (str): Dirección relativa del experimento en phyphox.
            intervaloMuestreo (float, optional): Intervalo de muestreo en segundos. Por defecto es 0.1.
        """
        self.__ip = ip
        self.__puerto = puerto
        self.__direccionRelativa = direccionRelativa
        self.__variables = variables
        self.__intervaloMuestreo = intervaloMuestreo
        self.__url = f"http://{ip}:{puerto}"

        self.__datos = [] #lista para almacenar los datos recolectados

        self.__fechaHoraInicio = None
        self.__nombreArchivo = None
        self.__midiendo = False

    #Métodos 

    def getIP(self):
        """
        Permite obtener la dirección IP del dispositivo phyphox.
        """
        return self.__ip

    def setIP(self, ip):
        """
        Permite cambiar la dirección IP del dispositivo phyphox y actualiza la URL.
        """
        self.__ip = ip
        self.__url = f"http://{ip}:{self.__puerto}" #Actualiza la URL con la nueva IP

    def getPuerto(self):
        """
        Permite obtener el puerto de acceso remoto del dispositivo phyphox.
        """
        return self.__puerto

    def setPuerto(self, puerto):
        """
        Permite cambiar el puerto de acceso remoto del dispositivo phyphox y actualiza la URL.
        """
        self.__puerto = puerto
        self.__url = f"http://{self.__ip}:{puerto}" #Actualiza la URL con el nuevo puerto    

    def getDireccionRelativa(self):
        """
        Permite obtener la dirección relativa del experimento en phyphox.
        """
        return self.__direccionRelativa

    def setDireccionRelativa(self, direccionRelativa):
        """
        Permite cambiar la dirección relativa del experimento en phyphox
        """
        self.__direccionRelativa = direccionRelativa
    
    def getVariables(self):
        """
        Permite obtener la lista de variables a recolectar.
        """
        return self.__variables

    def setVariables(self, variables):
        """
        Permite cambiar la lista de variables a recolectar.
        """
        self.__variables = variables

    def getIntervaloMuestreo(self):
        """
        Permite obtener el intervalo de muestreo.
        """
        return self.__intervaloMuestreo

    def setIntervaloMuestreo(self, intervaloMuestreo):
        """
        Permite cambiar el intervalo de muestreo.
        """
        self.__intervaloMuestreo = intervaloMuestreo

    def geturl(self):
        """permite obtener la url de acceso remoto del dispositivo phyphox."""
        return self.__url

    def seturl(self, ip, puerto, direccionRelativa):
        """Permite cambiar la url de acceso remoto del dispositivo phyphox."""
        self.__url = f"http://{ip}:{puerto}"

    def getDatos(self):
        """permite obtener los datos recolectados."""
        return self.__datos

    def setDatos(self, datos):
        """permite cambiar los datos recolectados."""
        self.__datos = datos

    def getFechaHoraInicio(self):
        """permite obtener la fecha y hora de inicio del experimento."""
        return self.__fechaHoraInicio

    def setFechaHoraInicio(self, fechaHora):
        """Permite cambiar la fehca y hora de inicio"""
        self.__fechaHoraInicio = fechaHora

    def getNombreArchivo(self):
        """permite obtener el nombre del archivo donde se guardarán los datos."""
        return self.__nombreArchivo

    def getMidiendo(self):
        """permite obtener el estado de medición."""
        return self.__midiendo

    def setMidiendo(self, midiendo):
        """permite cambiar el estado de medición."""
        self.__midiendo = midiendo

    def getNombreArchivo(self):
        """Devuelve el nombre del archivo"""
        return self.__nombreArchivo

    def setNombreArchivo(self, nombreArchivo):
        """Permite cambiar el nombre del archivo"""
        self.__nombreArchivo = nombreArchivo

    # Métodos para comunicarse con phyphox

    def _enviar_comando(self, comando):
        """Envía un comando de control a Phyphox (start, stop, clear).
            - start: Inicia la recolección de datos.
            - stop: Detiene la recolección de datos.
            - clear: Limpia los datos recolectados.
        """


        url = f"{self.geturl()}/control?cmd={comando}" # Construye la URL para enviar el comando a Phyphox
        try:
            respuesta = requests.get(url, timeout=5)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al enviar comando '{comando}' a Phyphox: {e}") # este print está solo para pruebas, hay que quitarlo cuando se haga la versión final
            return None

    def _obtener_datos(self):
        """Pide a Phyphox el contenido actual de los buffers de las variables."""
        variables_query = "&".join(self.getVariables()) # Construye la cadena de consulta con las variables a recolectar
        url = f"{self.geturl()}/get?{variables_query}"
        try:
            respuesta = requests.get(url, timeout=5)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener datos de Phyphox: {e}") # este print está solo para pruebas, hay que quitarlo cuando se haga la versión final
            return None

    # Control de mediciones
    def _iniciar_medicion(self):
        """Limpia buffers previos y arranca la medición en Phyphox."""
        self._enviar_comando("clear")
        resultado = self._enviar_comando("start")
        print("DEBUG - respuesta de 'start':", resultado)   # <- temporal
        if resultado is not None:
            self.setMidiendo(True)
            self.setFechaHoraInicio(datetime.now())
            print(f"Medición iniciada a las {self.getFechaHoraInicio().strftime('%Y-%m-%d %H:%M:%S')}")
        return resultado

    def _detener_medicion(self):
        """Detiene la medición en Phyphox."""
        resultado = self._enviar_comando("stop")
        self.setMidiendo(False)
        print("Medición detenida.") # este print está solo para pruebas, hay que quitarlo cuando se haga la versión final
        return resultado

    def _recolectar_datos(self, duracion_segundos):
        if not self.getMidiendo():
            self._iniciar_medicion()

        tiempo_final = time.time() + duracion_segundos

        while time.time() < tiempo_final:
            datos_json = self._obtener_datos()
            print("DEBUG - JSON recibido:", datos_json)   # <- temporal
            if datos_json is not None:
                self._procesar_datos_json(datos_json)
            time.sleep(self.getIntervaloMuestreo())

        self._detener_medicion()
        self._guardar_csv()

    # métodos para procesar y guardar datos
    def _procesar_datos_json(self, datos_json):
        """Extrae las listas de valores del JSON de Phyphox y las agrega a self.datos."""
        buffers = datos_json.get("buffer", {})
        datosObtenidos = []

        listas_variables = []
        for var in self.getVariables():
            info_variable = buffers.get(var, {})
            valores = info_variable.get("buffer", [])
            if not valores or valores[0] is None:
                return  # todavía no hay un valor real para esta variable
            listas_variables.append(valores)

        if not listas_variables:
            return

        cantidad_muestras = min(len(lista) for lista in listas_variables)

        for i in range(cantidad_muestras):
            fila = [listas_variables[idx][i] for idx in range(len(self.getVariables()))]
            datosObtenidos.append(fila)

        self.setDatos(self.getDatos() + datosObtenidos)

    def _guardar_csv(self):
        """Guarda self.__datos en un CSV dentro de self.direccion_relativa."""
        if not self.getDatos():
            print("No hay datos para guardar.") #este print es solo de prueba, hay que quitarlo en la versión final
            return None
 
        if not os.path.exists(self.getDireccionRelativa()):
            os.makedirs(self.getDireccionRelativa())
 
        fecha_str = self.getFechaHoraInicio().strftime("%Y-%m-%d")
        hora_str = self.getFechaHoraInicio().strftime("%H-%M-%S")
        self.setNombreArchivo(f"Acelerómetro{fecha_str}{hora_str}.csv")
 
        ruta_completa = os.path.join(self.getDireccionRelativa(), self.getNombreArchivo())
 
        with open(ruta_completa, mode="w", newline="", encoding="utf-8") as archivo_csv:
            escritor = csv.writer(archivo_csv)
            escritor.writerow(self.getVariables())
            escritor.writerows(self.getDatos())
 
        print(f"Datos guardados en: {ruta_completa}") # print de prueba, hay que quitarlo en la versión final
        return ruta_completa

        
if __name__ == "__main__":
    # Ejemplo de uso. La IP y el puerto aparecen en la pantalla de
    # "acceso remoto" de Phyphox cuando lo activas en el celular.
    recolector = RecolectorDatos(
        ip="192.168.1.29",
        variables=["accX", "accY", "accZ", "acc_time"],
        puerto=80,
        direccionRelativa="datos_experimentos",
    )
    recolector._recolectar_datos(duracion_segundos=5)