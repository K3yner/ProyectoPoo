import time
from datetime import datetime
import threading
import requests

from csv_manager import CSVManager


class RecolectorDatos:
    """
    Clase encargada de recolectar los datos del phyphox a través de la
    función acceso remoto.

    Necesita los paquetes:
        - time
        - datetime
        - threading
        - requests

    si no se tiene alguno de estos basta con ejecutar el comando:

        pip install {nombre paquete}

    para instalarlo.

    Correcciones aplicadas respecto a la versión anterior:
        - Se integró CSVManager para el guardado (ya no escribe CSV directamente).
        - _obtener_datos ahora usa un umbral sobre la variable de tiempo, así ya
          no se pierden ni se repiten muestras entre consultas (ver documentación
          de Phyphox sobre "/get" y el parámetro de threshold).
        - Se agregaron iniciar()/detener(), que corren la recolección en un hilo
          aparte, para poder controlarla con botones en vez de una duración fija.
        - Se eliminó el método getNombreArchivo duplicado y el método seturl,
          que dejaba el objeto en un estado inconsistente.
    """

    def __init__(self, ip, variables, puerto=8080, direccionRelativa="datos_experimento",
                 intervaloMuestreo=0.1, variableTiempo=None):
        """
        Inicializa la clase RecolectorDatos.

        Args:
            ip (str): Dirección IP del dispositivo phyphox.
            variables (list): Lista de variables a recolectar. Para el acelerómetro son accX, accY, accZ, acc_time
            puerto (int, optional): Puerto de acceso remoto. Por defecto es 8080 (Android).
                En iPhone, Phyphox usa por defecto el puerto 80.
            direccionRelativa (str): Dirección relativa donde se guardan los csv.
            intervaloMuestreo (float, optional): Intervalo de muestreo en segundos. Por defecto es 0.1.
            variableTiempo (str, optional): Nombre de la variable que actúa como referencia de
                tiempo (ej. "acc_time"). Si no se especifica, se asume la última de la lista.
        """
        self.__ip = ip
        self.__puerto = puerto
        self.__direccionRelativa = direccionRelativa
        self.__variables = variables
        self.__intervaloMuestreo = intervaloMuestreo
        self.__variableTiempo = variableTiempo or variables[-1]
        self.__url = f"http://{ip}:{puerto}"

        self.__datos = []
        self.__ultimoTiempo = 0

        self.__fechaHoraInicio = None
        self.__nombreArchivo = None
        self.__midiendo = False
        self.__hilo = None

        self.__csvManager = CSVManager(direccionRelativa)

    # Métodos

    def getIP(self):
        """Permite obtener la dirección IP del dispositivo phyphox."""
        return self.__ip

    def setIP(self, ip):
        """Permite cambiar la dirección IP del dispositivo phyphox y actualiza la URL."""
        self.__ip = ip
        self.__url = f"http://{ip}:{self.__puerto}"

    def getPuerto(self):
        """Permite obtener el puerto de acceso remoto del dispositivo phyphox."""
        return self.__puerto

    def setPuerto(self, puerto):
        """Permite cambiar el puerto de acceso remoto del dispositivo phyphox y actualiza la URL."""
        self.__puerto = puerto
        self.__url = f"http://{self.__ip}:{puerto}"

    def getDireccionRelativa(self):
        """Permite obtener la dirección relativa del experimento en phyphox."""
        return self.__direccionRelativa

    def setDireccionRelativa(self, direccionRelativa):
        """Permite cambiar la dirección relativa donde se guardan los csv."""
        self.__direccionRelativa = direccionRelativa
        self.__csvManager.set_direccion_relativa(direccionRelativa)

    def getVariables(self):
        """Permite obtener la lista de variables a recolectar."""
        return self.__variables

    def setVariables(self, variables):
        """Permite cambiar la lista de variables a recolectar."""
        self.__variables = variables

    def getIntervaloMuestreo(self):
        """Permite obtener el intervalo de muestreo."""
        return self.__intervaloMuestreo

    def setIntervaloMuestreo(self, intervaloMuestreo):
        """Permite cambiar el intervalo de muestreo."""
        self.__intervaloMuestreo = intervaloMuestreo

    def geturl(self):
        """Permite obtener la url de acceso remoto del dispositivo phyphox."""
        return self.__url

    def getDatos(self):
        """Permite obtener los datos recolectados."""
        return self.__datos

    def setDatos(self, datos):
        """Permite cambiar los datos recolectados."""
        self.__datos = datos

    def getFechaHoraInicio(self):
        """Permite obtener la fecha y hora de inicio del experimento."""
        return self.__fechaHoraInicio

    def setFechaHoraInicio(self, fechaHora):
        """Permite cambiar la fecha y hora de inicio."""
        self.__fechaHoraInicio = fechaHora

    def getNombreArchivo(self):
        """Devuelve el nombre del archivo donde se guardaron los datos."""
        return self.__nombreArchivo

    def setNombreArchivo(self, nombreArchivo):
        """Permite cambiar el nombre del archivo."""
        self.__nombreArchivo = nombreArchivo

    def getMidiendo(self):
        """Permite obtener el estado de medición."""
        return self.__midiendo

    def setMidiendo(self, midiendo):
        """Permite cambiar el estado de medición."""
        self.__midiendo = midiendo

    # Control de mediciones -- interfaz pública para usar con botones

    def iniciar(self):
        """
        Inicia la medición en un hilo aparte, para no bloquear el programa
        mientras se recolectan datos. Pensado para conectarse a un botón "Iniciar".
        """
        if self.getMidiendo():
            print("Ya hay una medición en curso.")
            return

        self.__ultimoTiempo = 0
        self.setDatos([])
        resultado = self._iniciar_medicion()
        if resultado is None:
            print("No se pudo iniciar la medición en Phyphox.")
            return

        self.__hilo = threading.Thread(target=self._bucle_recoleccion, daemon=True)
        self.__hilo.start()

    def detener(self):
        """
        Detiene la medición, espera a que el hilo de recolección termine, y
        guarda los datos recolectados en un CSV. Pensado para conectarse a
        un botón "Detener".

        Returns:
            str | None: ruta del CSV guardado, o None si no había datos.
        """
        if not self.getMidiendo():
            print("No hay ninguna medición en curso.")
            return None

        self.setMidiendo(False)
        if self.__hilo is not None:
            self.__hilo.join()

        self._detener_medicion()
        return self._guardar_csv()

    # Métodos internos para comunicarse con phyphox

    def _enviar_comando(self, comando):
        """Envía un comando de control a Phyphox (start, stop, clear)."""
        url = f"{self.geturl()}/control?cmd={comando}"
        try:
            respuesta = requests.get(url, timeout=5)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al enviar comando '{comando}' a Phyphox: {e}")
            return None

    def _obtener_datos(self):
        """
        Pide a Phyphox solo los valores nuevos desde la última consulta, usando
        la variable de tiempo como referencia (threshold). Esto evita perder
        muestras cuando el sensor produce datos más rápido que intervaloMuestreo,
        que era lo que pasaba al pedir solo el último valor de cada variable.
        """
        partes = [f"{self.__variableTiempo}={self.__ultimoTiempo}"]
        for var in self.getVariables():
            if var == self.__variableTiempo:
                continue
            partes.append(f"{var}={self.__ultimoTiempo}%7C{self.__variableTiempo}")

        variables_query = "&".join(partes)
        url = f"{self.geturl()}/get?{variables_query}"

        try:
            respuesta = requests.get(url, timeout=5)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener datos de Phyphox: {e}")
            return None

    def _iniciar_medicion(self):
        """Limpia buffers previos y arranca la medición en Phyphox."""
        self._enviar_comando("clear")
        resultado = self._enviar_comando("start")
        if resultado is not None:
            self.setMidiendo(True)
            self.setFechaHoraInicio(datetime.now())
            print(f"Medición iniciada a las {self.getFechaHoraInicio().strftime('%Y-%m-%d %H:%M:%S')}")
        return resultado

    def _detener_medicion(self):
        """Detiene la medición en Phyphox."""
        resultado = self._enviar_comando("stop")
        self.setMidiendo(False)
        print("Medición detenida.")
        return resultado

    def _bucle_recoleccion(self):
        """Corre en un hilo aparte mientras getMidiendo() sea True."""
        while self.getMidiendo():
            datos_json = self._obtener_datos()
            if datos_json is not None:
                self._procesar_datos_json(datos_json)
            time.sleep(self.getIntervaloMuestreo())

    def _procesar_datos_json(self, datos_json):
        """Extrae las listas de valores nuevos del JSON y las agrega a self.datos."""
        buffers = datos_json.get("buffer", {})
        listas_variables = []

        for var in self.getVariables():
            info_variable = buffers.get(var, {})
            valores = info_variable.get("buffer", [])
            listas_variables.append(valores)

        cantidad_muestras = min((len(lista) for lista in listas_variables), default=0)
        if cantidad_muestras == 0:
            return  # todavía no hay muestras nuevas

        datosObtenidos = []
        for i in range(cantidad_muestras):
            fila = [listas_variables[idx][i] for idx in range(len(self.getVariables()))]
            datosObtenidos.append(fila)

        self.setDatos(self.getDatos() + datosObtenidos)

        indice_tiempo = self.getVariables().index(self.__variableTiempo)
        valores_tiempo_nuevos = listas_variables[indice_tiempo]
        if valores_tiempo_nuevos:
            self.__ultimoTiempo = valores_tiempo_nuevos[-1]

    def _guardar_csv(self):
        """Guarda self.__datos en un CSV, delegando la escritura a CSVManager."""
        if not self.getDatos():
            print("No hay datos para guardar.")
            return None

        fecha_str = self.getFechaHoraInicio().strftime("%Y-%m-%d")
        hora_str = self.getFechaHoraInicio().strftime("%H-%M-%S")
        nombre_archivo = f"Acelerometro_{fecha_str}_{hora_str}.csv"

        ruta_completa = self.__csvManager.guardar(self.getDatos(), self.getVariables(), nombre_archivo)
        self.setNombreArchivo(nombre_archivo)

        print(f"Datos guardados en: {ruta_completa}")
        return ruta_completa

