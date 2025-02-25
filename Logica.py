import asyncio
import queue
import threading
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import pytz
from telegram import Bot
from telegram.request import HTTPXRequest
import tkinter as tk
import time
import logging
import tempfile
import os
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Usar el backend 'Agg' para evitar problemas con hilos
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Logica:
    def __init__(self, root, indicadores):
        """Inicializa la lógica del bot de trading."""
        # Configurar el bot de Telegram
        request = HTTPXRequest()
        self.bot = Bot(token="7975954346:AAGZml5vbuT5cTt6d2i9z11MvqoltEHfbWM", request=request)
        
        self.ultima_senal_enviada = None  # Última señal enviada
        self.mensaje_queue = queue.Queue()  # Cola de mensajes
        self.procesando_mensajes = False  # Bandera de procesamiento
        self.root = root  # Guardar la referencia de la ventana Tkinter
        self.indicadores = indicadores  # Guardar la instancia de Indicadores

        # Variables para limitar el envío de mensajes
        self.contador_mensajes = 0  # Contador de mensajes enviados
        self.tiempo_inicio_intervalo = None  # Tiempo de inicio del intervalo de 2 minutos

        # Crear un nuevo loop de eventos de asyncio
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.loop_thread.start()

        # Agregar tarea inicial
        self.run_async_task(self.enviar_mensaje_inicio())

    def run_loop(self):
        """Ejecuta el loop de asyncio en un hilo separado."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_async_task(self, coro):
        """Ejecuta una tarea asincrónica desde otro hilo de forma segura."""
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def enviar_mensaje_inicio(self):
        """Envía un mensaje de inicio al chat de Telegram."""
        mensaje = "✅ El programa de trading se ha iniciado correctamente."
        self.mensaje_queue.put(mensaje)
        await self.procesar_cola_mensajes()

    async def enviar_alerta(self, tipo, divisa):
        """Envía una alerta de compra o venta a Telegram junto con un gráfico generado."""
        try:
            # Inicializar tiempo_actual fuera del bloque condicional
            tiempo_actual = time.time()

            if self.tiempo_inicio_intervalo is not None:
                tiempo_transcurrido = tiempo_actual - self.tiempo_inicio_intervalo

                # Reiniciar el contador si han pasado 5 minutos
                if tiempo_transcurrido >= 300:  # 300 segundos = 5 minutos
                    self.contador_mensajes = 0
                    self.tiempo_inicio_intervalo = tiempo_actual

            # Si el contador es menor que 2, enviar el mensaje y el gráfico
            if self.contador_mensajes < 2:
                mensajes = {
                    "compra": f"📈 Momento de Comprar {divisa}",
                    "venta": f"📉 Momento de Vender {divisa}",
                }
                mensaje = mensajes.get(tipo, f"⚠️ Operación desconocida en {divisa}")
                self.mensaje_queue.put(mensaje)

                # Generar el gráfico y guardarlo en la carpeta
                ruta_grafico = self.generar_grafico(divisa)
                if ruta_grafico:
                    with open(ruta_grafico, "rb") as archivo:
                        self.mensaje_queue.put((archivo, ruta_grafico))  # Añadir el archivo y su ruta a la cola

                await self.procesar_cola_mensajes()

                # Incrementar el contador y registrar el tiempo de inicio del intervalo
                self.contador_mensajes += 1
                if self.tiempo_inicio_intervalo is None:
                    self.tiempo_inicio_intervalo = tiempo_actual
            else:
                logging.info("🟡 Límite de mensajes alcanzado. Esperando 5 minutos...")
        except Exception as e:
            logging.error(f"Error en enviar_alerta: {e}")

    def generar_grafico(self, divisa):
        """Genera un gráfico con los datos de la divisa y lo guarda en la carpeta de gráficos."""
        try:
            # Obtener datos del mercado (últimas 24 horas)
            data = self.indicadores.obtener_datos(divisa, "1H", 24)  # Usar self.indicadores
            if data.empty:
                raise ValueError("No se obtuvieron datos del servidor. Verifica el símbolo y el timeframe.")

            # Calcular indicadores
            data = self.indicadores.calcular_indicadores(data)

            # Crear una nueva figura y ejes
            fig, ax = plt.subplots(figsize=(8, 4))

            # Dibujar el gráfico
            ax.plot(data['time'], data['close'], label="Precio", color='black')
            ax.plot(data['time'], data['EMA_8'], label="EMA 8", color='orange')
            ax.plot(data['time'], data['EMA_21'], label="EMA 21", color='green')
            ax.plot(data['time'], data['EMA_100'], label="EMA 100", color='red')

            # Configurar los ejes X e Y con transparencia
            ax.spines['bottom'].set_alpha(0.5)  # Transparencia del eje X (inferior)
            ax.spines['top'].set_alpha(0.5)     # Transparencia del eje X (superior)
            ax.spines['left'].set_alpha(0.5)    # Transparencia del eje Y (izquierdo)
            ax.spines['right'].set_alpha(0.5)   # Transparencia del eje Y (derecho)

            # Ajustar el grosor de las líneas de los ejes
            ax.spines['bottom'].set_linewidth(0.8)
            ax.spines['top'].set_linewidth(0.8)
            ax.spines['left'].set_linewidth(0.8)
            ax.spines['right'].set_linewidth(0.8)

            # Agregar etiquetas a los ejes
            ax.set_xlabel("Tiempo", fontsize=9, alpha=0.8)
            ax.set_ylabel("Precio", fontsize=9, alpha=0.8)

            # Agregar el símbolo de la divisa en el gráfico
            ax.text(
                0.02, 0.95, f"Símbolo: {divisa}", transform=ax.transAxes,
                fontsize=9, color='blue', backgroundcolor='white', alpha=0.8
            )

            # Formatear el eje x para mostrar horas en UTC-5
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=pytz.timezone('America/New_York')))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))

            # Rotar etiquetas del eje x
            plt.xticks(rotation=45)

            # Añadir leyenda
            ax.legend()

            # Ajustar el diseño de la figura manualmente
            plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)

            # Ruta para la carpeta donde guardar gráficos
            carpeta_graficos = r"D:\LENOVO\Desktop\Graficos_Trading"

            # Crear la carpeta si no existe
            if not os.path.exists(carpeta_graficos):
                os.makedirs(carpeta_graficos)

            # Crear el nombre del archivo
            fecha_hora = datetime.now(pytz.timezone('America/New_York')).strftime("%Y%m%d_%H%M%S")  # Hora en UTC-5
            nombre_archivo = f"{divisa}_{fecha_hora}.jpg"  # Formato: DIVISA_fecha_horario.jpg
            ruta_grafico = os.path.join(carpeta_graficos, nombre_archivo)

            # Guardar el gráfico en la carpeta
            plt.savefig(ruta_grafico, format="jpg", dpi=100)
            plt.close(fig)  # Cerrar la figura para liberar memoria

            return ruta_grafico
        except Exception as e:
            logging.error(f"Error al generar el gráfico: {e}")
            return None

    async def procesar_cola_mensajes(self):
        """Procesa los mensajes en la cola y los envía a Telegram."""
        if not self.procesando_mensajes:
            self.procesando_mensajes = True
            while not self.mensaje_queue.empty():
                mensaje = self.mensaje_queue.get()
                try:
                    if isinstance(mensaje, tuple):  # Si es un archivo
                        archivo, ruta_grafico = mensaje
                        await self.bot.send_photo(chat_id="-4731258133", photo=archivo)
                        logging.info("Gráfico enviado a Telegram.")
                        archivo.close()  # Cerrar el archivo
                    else:  # Si es un mensaje de texto
                        await self.bot.send_message(chat_id="-4731258133", text=mensaje)
                        logging.info(f"Mensaje enviado a Telegram: {mensaje}")
                except Exception as e:
                    logging.error(f"Error enviando mensaje o archivo por Telegram: {e}")
            self.procesando_mensajes = False

    def calcular_indicadores(self, data):
        """Calcula indicadores como EMA y señales de compra/venta."""
        if data.empty:
            raise ValueError("❌ El dataframe está vacío. No se pueden calcular indicadores.")
        
        # Calcular las EMAs
        data['EMA_8'] = data['close'].ewm(span=8).mean()
        data['EMA_21'] = data['close'].ewm(span=21).mean()
        
        # Determinar la señal actual
        data['Signal'] = np.where(data['EMA_8'] > data['EMA_21'], 'compra', 'venta')
        
        # Detectar cambios en la señal
        data['Signal_Change'] = data['Signal'].ne(data['Signal'].shift())
        
        logging.info(f"📊 Última señal: {data['Signal'].iloc[-1]}")
        logging.info(f"🔄 Cambio de señal: {data['Signal_Change'].iloc[-1]}")
        
        return data


# === PRUEBA DE LA CLASE LOGICA ===
if __name__ == "__main__":
    root = tk.Tk()  # Crear ventana Tkinter
    bot_trading = Logica(root)  # Inicializar la clase
    root.mainloop()  # Ejecutar la interfaz gráfica