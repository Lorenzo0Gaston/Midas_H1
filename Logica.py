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


class Logica:
    def __init__(self, root):
        """Inicializa la lógica del bot de trading"""
        # Configurar el bot de Telegram
        request = HTTPXRequest()
        self.bot = Bot(token="7975954346:AAGZml5vbuT5cTt6d2i9z11MvqoltEHfbWM", request=request)
        
        self.ultima_senal_enviada = None  # Última señal enviada
        self.mensaje_queue = queue.Queue()  # Cola de mensajes
        self.procesando_mensajes = False  # Bandera de procesamiento
        self.root = root  # Guardar la referencia de la ventana Tkinter

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
        """Ejecuta el loop de asyncio en un hilo separado"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_async_task(self, coro):
        """Ejecuta una tarea asincrónica desde otro hilo de forma segura"""
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def enviar_mensaje_inicio(self):
        """Envía un mensaje de inicio al chat de Telegram."""
        mensaje = "✅ El programa de trading se ha iniciado correctamente."
        self.mensaje_queue.put(mensaje)
        await self.procesar_cola_mensajes()

    async def enviar_alerta(self, tipo, divisa):
        """Envía una alerta de compra o venta a Telegram."""
        # Verificar si ha pasado el intervalo de 2 minutos
        if self.tiempo_inicio_intervalo is not None:
            tiempo_actual = time.time()
            tiempo_transcurrido = tiempo_actual - self.tiempo_inicio_intervalo

            # Reiniciar el contador si han pasado 2 minutos
                self.contador_mensajes = 0
                self.tiempo_inicio_intervalo = tiempo_actual

        # Si el contador es menor que 2, enviar el mensaje
        if self.contador_mensajes < 2:
            mensajes = {
                "compra": f"📈 Momento de Comprar {divisa}",
                "venta": f"📉 Momento de Vender {divisa}",
            }
            mensaje = mensajes.get(tipo, f"⚠️ Operación desconocida en {divisa}")
            self.mensaje_queue.put(mensaje)
            await self.procesar_cola_mensajes()

            # Incrementar el contador y registrar el tiempo de inicio del intervalo
            self.contador_mensajes += 1
            if self.tiempo_inicio_intervalo is None:
                self.tiempo_inicio_intervalo = time.time()
        else:
            print("🟡 Límite de mensajes alcanzado. Esperando 2 minutos...")

    async def procesar_cola_mensajes(self):
        """Procesa los mensajes en la cola y los envía a Telegram."""
        if not self.procesando_mensajes:
            self.procesando_mensajes = True
            while not self.mensaje_queue.empty():
                mensaje = self.mensaje_queue.get()
                try:
                    await self.bot.send_message(chat_id="-4731258133", text=mensaje)
                    print(f"Mensaje enviado a Telegram: {mensaje}")
                except Exception as e:
                    print(f"Error enviando mensaje por Telegram: {e}")
            self.procesando_mensajes = False

    async def ejecutar_trading_en_tiempo_real(self, simbolo, timeframe, lote, stop_loss, take_profit):
        """Ejecuta el trading en tiempo real en un bucle asincrónico."""
        print("✅ Iniciando el bucle de trading en tiempo real...")
        while True:
            print("🔄 Obteniendo datos del mercado...")
            rates = mt5.copy_rates_from_pos(simbolo, timeframe, 0, 1)
            if rates is not None:
                data = pd.DataFrame(rates)
                data['time'] = pd.to_datetime(data['time'], unit='s')
                data = self.calcular_indicadores(data)

                ultima_senal = data['Signal'].iloc[-1]  # Última señal
                signal_change = data['Signal_Change'].iloc[-1]  # Cambio de señal

                if signal_change and ultima_senal != self.ultima_senal_enviada:
                    print(f"⚡ Cambio de señal detectado: {ultima_senal}")
                    await self.enviar_alerta(ultima_senal, simbolo)
                    self.ultima_senal_enviada = ultima_senal
                else:
                    print(f"🟡 No hay cambio de señal. Última señal: {self.ultima_senal_enviada}")

            await asyncio.sleep(60)  # Esperar 1 minuto antes de la siguiente iteración

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
        
        print(f"📊 Última señal: {data['Signal'].iloc[-1]}")
        print(f"🔄 Cambio de señal: {data['Signal_Change'].iloc[-1]}")
        
        return data


# === PRUEBA DE LA CLASE LOGICA ===
if __name__ == "__main__":
    root = tk.Tk()  # Crear ventana Tkinter
    bot_trading = Logica(root)  # Inicializar la clase
    root.mainloop()  # Ejecutar la interfaz gráfica