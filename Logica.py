import asyncio
import queue
import threading
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from telegram import Bot
from telegram.request import HTTPXRequest
import tkinter as tk
import time
from PIL import ImageGrab
import io
import pygetwindow as gw
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Logica:
    def __init__(self, root):
        request = HTTPXRequest()
        self.bot = Bot(token="7975954346:AAGZml5vbuT5cTt6d2i9z11MvqoltEHfbWM", request=request)
        self.ultima_senal_enviada = None
        self.mensaje_queue = queue.Queue()
        self.procesando_mensajes = False
        self.root = root
        self.contador_mensajes = 0
        self.tiempo_inicio_intervalo = None
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.loop_thread.start()
        self.run_async_task(self.enviar_mensaje_inicio())

    def run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_async_task(self, coro):
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def enviar_mensaje_inicio(self):
        mensaje = "✅ El programa de trading se ha iniciado correctamente."
        self.mensaje_queue.put(mensaje)
        await self.procesar_cola_mensajes()

    async def enviar_alerta(self, tipo, divisa):
        try:
            if self.tiempo_inicio_intervalo is not None:
                tiempo_actual = time.time()
                tiempo_transcurrido = tiempo_actual - self.tiempo_inicio_intervalo
                if tiempo_transcurrido >= 300:
                    self.contador_mensajes = 0
                    self.tiempo_inicio_intervalo = tiempo_actual
            if self.contador_mensajes < 2:
                mensajes = {"compra": f" Momento de Comprar {divisa}", "venta": f" Momento de Vender {divisa}"}
                mensaje = mensajes.get(tipo, f"⚠️ Operación desconocida en {divisa}")
                self.mensaje_queue.put(mensaje)
                captura = await asyncio.to_thread(self.capturar_ventana_grafico, divisa)
                if captura:
                    self.mensaje_queue.put(captura)
                await self.procesar_cola_mensajes()
                self.contador_mensajes += 1
                if self.tiempo_inicio_intervalo is None:
                    self.tiempo_inicio_intervalo = tiempo_actual
            else:
                logging.info("🟡 Límite de mensajes alcanzado. Esperando 5 minutos...")
        except Exception as e:
            logging.error(f"Error en enviar_alerta: {e}")

    def capturar_ventana_grafico(self, divisa):
        try:
            ventanas = gw.getWindowsWithTitle(f"Gráficos de Trading - {divisa}")
            if ventanas:
                ventana = ventanas[0]
                left, top, right, bottom = ventana.left, ventana.top, ventana.right, ventana.bottom
                captura = ImageGrab.grab(bbox=(left, top, right, bottom))
                imagen_bytes = io.BytesIO()
                captura.save(imagen_bytes, format="PNG")
                imagen_bytes.seek(0)
                return imagen_bytes
            else:
                logging.warning(f"No se encontró la ventana del gráfico para {divisa}.")
                return None
        except Exception as e:
            logging.error(f"Error al capturar la ventana del gráfico: {e}")
            return None

    async def procesar_cola_mensajes(self):
        if not self.procesando_mensajes:
            self.procesando_mensajes = True
            while not self.mensaje_queue.empty():
                mensaje = self.mensaje_queue.get()
                try:
                    if isinstance(mensaje, io.BytesIO):
                        await self.bot.send_photo(chat_id="-4731258133", photo=mensaje)
                        logging.info("Captura de la ventana del gráfico enviada a Telegram.")
                    else:
                        await self.bot.send_message(chat_id="-4731258133", text=mensaje)
                        logging.info(f"Mensaje enviado a Telegram: {mensaje}")
                except Exception as e:
                    logging.error(f"Error enviando mensaje o imagen por Telegram: {e}")
            self.procesando_mensajes = False

    async def ejecutar_trading_en_tiempo_real(self, simbolo, timeframe, lote, stop_loss, take_profit):
        logging.info("✅ Iniciando el bucle de trading en tiempo real...")
        while True:
            logging.info(" Obteniendo datos del mercado...")
            rates = mt5.copy_rates_from_pos(simbolo, timeframe, 0, 1)
            if rates is not None:
                data = pd.DataFrame(rates)
                data['time'] = pd.to_datetime(data['time'], unit='s')
                data = self.calcular_indicadores(data)
                ultima_senal = data['Signal'].iloc[-1]
                signal_change = data['Signal_Change'].iloc[-1]
                if signal_change and ultima_senal != self.ultima_senal_enviada:
                    logging.info(f"⚡ Cambio de señal detectado: {ultima_senal}")
                    await self.enviar_alerta(ultima_senal, simbolo)
                    self.ultima_senal_enviada = ultima_senal
                else:
                    logging.info(f"🟡 No hay cambio de señal. Última señal: {self.ultima_senal_enviada}")
            await asyncio.sleep(60)

    def calcular_indicadores(self, data):
        if data.empty:
            raise ValueError("❌ El dataframe está vacío. No se pueden calcular indicadores.")
        data['EMA_8'] = data['close'].ewm(span=8).mean()
        data['EMA_21'] = data['close'].ewm(span=21).mean()
        data['Signal'] = np.where(data['EMA_8'] > data['EMA_21'], 'compra', 'venta')
        data['Signal_Change'] = data['Signal'].ne(data['Signal'].shift())
        logging.info(f" Última señal: {data['Signal'].iloc[-1]}")
        logging.info(f" Cambio de señal: {data['Signal_Change'].iloc[-1]}")
        return data

if __name__ == "__main__":
    root = tk.Tk()
    bot_trading = Logica(root)
    root.mainloop()