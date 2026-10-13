import os
import time
from datetime import datetime
 
import pandas as pd
import requests
 
 
class RecolectorDatos:
    """
    Clase encargada de recolectar los datos de phyphox a través de la
    función de acceso remoto.
 
    Los datos recolectados se guardan en un pandas.DataFrame cuyas columnas
    son exactamente las variables pedidas a phyphox (accX, accY, accZ,
    acc_time). Así, el resto del programa accede a cada columna por su
    NOMBRE y no por su posición.
 
    Necesita los paquetes:
        - pandas
        - requests
 
    Si no se tiene alguno basta con ejecutar:  pip install {nombre paquete}
    """
 
    def __init__(self, ip, variables, puerto=80, direccionRelativa="datos_experimento", intervaloMuestreo=0.1):
        """
        Args:
            ip (str): Dirección IP del dispositivo phyphox.
            variables (list): Variables a recolectar. Para el acelerómetro: accX, accY, accZ, acc_time
            puerto (int, optional): Puerto de acceso remoto (el que muestra phyphox en pantalla).
            direccionRelativa (str): Carpeta local donde se guardan los CSV.
            intervaloMuestreo (float, optional): Intervalo entre consultas en segundos.
        """
        self.__ip = ip
        self.__puerto = puerto
        self.__direccionRelativa = direccionRelativa
        self.__variables = variables
        self.__intervaloMuestreo = intervaloMuestreo
        self.__url = f"http://{ip}:{puerto}"
 
        # DataFrame vacío con las columnas esperadas
        self.__datos = pd.DataFrame(columns=variables)
 
        self.__fechaHoraInicio = None
        self.__nombreArchivo = None
        self.__midiendo = False
 
    # ------------------------------------------------------------------ #
    # Getters / setters
    # ------------------------------------------------------------------ #
 
    def getIP(self):
        return self.__ip
 
    def setIP(self, ip):
        self.__ip = ip
        self.__url = f"http://{ip}:{self.__puerto}"
 
    def getPuerto(self):
        return self.__puerto
 
    def setPuerto(self, puerto):
        self.__puerto = puerto
        self.__url = f"http://{self.__ip}:{puerto}"
 
    def getDireccionRelativa(self):
        return self.__direccionRelativa
 
    def setDireccionRelativa(self, direccionRelativa):
        self.__direccionRelativa = direccionRelativa
 
    def getVariables(self):
        return self.__variables
 
    def setVariables(self, variables):
        self.__variables = variables
 
    def getIntervaloMuestreo(self):
        return self.__intervaloMuestreo
 
    def setIntervaloMuestreo(self, intervaloMuestreo):
        self.__intervaloMuestreo = intervaloMuestreo
 
    def geturl(self):
        return self.__url
 
    def seturl(self, ip, puerto):
        self.__url = f"http://{ip}:{puerto}"
 
    def getDatos(self):
        """Devuelve el DataFrame con los datos recolectados."""
        return self.__datos
 
    def setDatos(self, datos):
        """Recibe un DataFrame con los datos recolectados."""
        self.__datos = datos
 
    def hayDatos(self):
        """True si el DataFrame tiene al menos una fila."""
        return not self.__datos.empty
 
    def getFechaHoraInicio(self):
        return self.__fechaHoraInicio
 
    def setFechaHoraInicio(self, fechaHora):
        self.__fechaHoraInicio = fechaHora
 
    def getMidiendo(self):
        return self.__midiendo
 
    def setMidiendo(self, midiendo):
        self.__midiendo = midiendo
 
    def getNombreArchivo(self):
        return self.__nombreArchivo
 
    def setNombreArchivo(self, nombreArchivo):
        self.__nombreArchivo = nombreArchivo
 
    # ------------------------------------------------------------------ #
    # Comunicación con phyphox
    # ------------------------------------------------------------------ #
 
    def _enviar_comando(self, comando):
        """Envía un comando de control a phyphox (start, stop, clear)."""
        url = f"{self.geturl()}/control?cmd={comando}"
        try:
            respuesta = requests.get(url, timeout=5)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.exceptions.RequestException:
            return None
 
    def _obtener_datos(self):
        """
        Pide a phyphox el contenido COMPLETO de los buffers.
 
        Importante: si se pide solo "?accX&accY", phyphox devuelve únicamente
        el ÚLTIMO valor de cada buffer. Para obtener todas las muestras
        tomadas desde el "start" hay que pedir "?accX=full&accY=full...".
        """
        variables_query = "&".join(f"{var}=full" for var in self.getVariables())
        url = f"{self.geturl()}/get?{variables_query}"
        try:
            respuesta = requests.get(url, timeout=10)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.exceptions.RequestException:
            return None
 
    # ------------------------------------------------------------------ #
    # Control de mediciones
    # ------------------------------------------------------------------ #
 
    def _iniciar_medicion(self):
        """Limpia buffers previos (en phyphox y localmente) y arranca la medición."""
        self._enviar_comando("clear")
        resultado = self._enviar_comando("start")
        self.setDatos(pd.DataFrame(columns=self.getVariables()))
        self.setNombreArchivo(None)
        if resultado is not None:
            self.setMidiendo(True)
            self.setFechaHoraInicio(datetime.now())
        return resultado
 
    def _detener_medicion(self):
        """Detiene la medición en phyphox."""
        resultado = self._enviar_comando("stop")
        self.setMidiendo(False)
        return resultado
 
    def _descargar_datos(self):
        """Descarga el buffer completo de phyphox y lo guarda como DataFrame."""
        datos_json = self._obtener_datos()
        if datos_json is None:
            return False
        self._procesar_datos_json(datos_json)
        return self.hayDatos()
 
    def _recolectar_datos(self, duracion_segundos):
        """Mide durante 'duracion_segundos', descarga todo y guarda el CSV."""
        if not self.getMidiendo():
            self._iniciar_medicion()
 
        time.sleep(duracion_segundos)
 
        self._detener_medicion()
        self._descargar_datos()
        return self._guardar_csv()
 
    # ------------------------------------------------------------------ #
    # Procesamiento y guardado
    # ------------------------------------------------------------------ #
 
    def _procesar_datos_json(self, datos_json):
        """
        Convierte el JSON de phyphox en un DataFrame.
 
        - Cada variable se vuelve una columna (por nombre).
        - Si los buffers tienen distinto largo se recortan al más corto.
        - Los valores nulos / no numéricos se eliminan.
        Como se pide el buffer completo, el DataFrame REEMPLAZA a los datos
        anteriores (no se concatena, así no se duplican filas).
        """
        buffers = datos_json.get("buffer", {})
 
        columnas = {}
        for var in self.getVariables():
            valores = buffers.get(var, {}).get("buffer", [])
            if not valores:
                return  # esa variable todavía no tiene datos
            columnas[var] = valores
 
        largo = min(len(v) for v in columnas.values())
        df = pd.DataFrame({var: valores[:largo] for var, valores in columnas.items()})
 
        df = df.apply(pd.to_numeric, errors="coerce").dropna().reset_index(drop=True)
        self.setDatos(df)
 
    def _guardar_csv(self):
        """Guarda el DataFrame en un CSV dentro de la carpeta de datos."""
        if not self.hayDatos():
            return None
 
        if self.getFechaHoraInicio() is None:
            self.setFechaHoraInicio(datetime.now())
 
        os.makedirs(self.getDireccionRelativa(), exist_ok=True)
 
        fecha_str = self.getFechaHoraInicio().strftime("%Y-%m-%d")
        hora_str = self.getFechaHoraInicio().strftime("%H-%M-%S")
        self.setNombreArchivo(f"Acelerometro_{fecha_str}_{hora_str}.csv")
 
        ruta_completa = os.path.join(self.getDireccionRelativa(), self.getNombreArchivo())
        self.getDatos().to_csv(ruta_completa, index=False, encoding="utf-8")
        return ruta_completa
 
 
if __name__ == "__main__":
    # La IP y el puerto aparecen en la pantalla de "acceso remoto" de phyphox.
    recolector = RecolectorDatos(
        ip="192.168.1.29",
        variables=["accX", "accY", "accZ", "acc_time"],
        puerto=80,
        direccionRelativa="datos_experimento",
    )
    ruta = recolector._recolectar_datos(duracion_segundos=5)
    print("Archivo:", ruta)
    print(recolector.getDatos().head())