from inspect import isframe
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import pandas as pd
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from Logica import Logica
from Indicador import Indicadores

class AplicacionTrading:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplicación de Trading")
        self.indicadores = Indicadores()
        self.logica = Logica(self.root)

        self.divisas = ["XAUUSD", "AUDUSD", "USDCAD", "EURUSD", "GBPUSD", 
                         "USO", "USDJPY", "NZDUSD", "GBPCHF", "US30", "US500M"]
        
        self.frame_ordenes = tk.Frame(root)
        self.frame_ordenes.pack(side=tk.LEFT, padx=10)

        self.label_simbolo = tk.Label(self.frame_ordenes, text="Seleccionar divisas:")
        self.label_simbolo.grid(row=0, column=0)

        self.combo_divisas = ttk.Combobox(self.frame_ordenes, values=self.divisas)
        self.combo_divisas.grid(row=0, column=1)
        self.combo_divisas.set("XAUUSD")

        self.label_timeframe = tk.Label(self.frame_ordenes, text="Timeframe:")
        self.label_timeframe.grid(row=1, column=0)

        self.combo_timeframe = ttk.Combobox(self.frame_ordenes, values=["1H", "4H", "1D"])
        self.combo_timeframe.grid(row=1, column=1)
        self.combo_timeframe.set("1H")

        self.boton_graficar = tk.Button(self.frame_ordenes, text="Añadir Gráfico", command=self.añadir_grafico)
        self.boton_graficar.grid(row=2, column=0, columnspan=2)
        
        self.ventanas_graficos = []
        self.ventana_ancho = 1200
        self.ventana_alto = 800
        self.intervalo_actualizacion = 5000

        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_loop, args=(self.loop,), daemon=True).start()
        self.executor = ThreadPoolExecutor(max_workers=4)

    def start_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def añadir_grafico(self):
        divisa = self.combo_divisas.get()
        timeframe = self.combo_timeframe.get()  # Definir timeframe aquí
        
        for ventana in self.ventanas_graficos:
            if divisa in ventana["divisas"]:
                messagebox.showwarning("Advertencia", f"La divisa {divisa} ya está siendo mostrada.")
                return
        if not self.ventanas_graficos or len(self.ventanas_graficos[-1]["divisas"]) >= 4:
            nueva_ventana = tk.Toplevel(self.root)
            nueva_ventana.title("Gráficos de Trading")
            nueva_ventana.geometry(f"{self.ventana_ancho}x{self.ventana_alto}")
            frame_graficos = tk.Frame(nueva_ventana)
            frame_graficos.pack()
            self.ventanas_graficos.append({"ventana": nueva_ventana, "frame_graficos": frame_graficos, "divisas": [], "graficos": {}})
        ventana_actual = self.ventanas_graficos[-1]
        ventana_actual["divisas"].append(divisa)
        self.mostrar_grafico(ventana_actual, divisa, timeframe)
        self.root.after(self.intervalo_actualizacion, lambda ventana=ventana_actual, divisa=divisa, timeframe=timeframe: self.actualizar_grafico(ventana, divisa, timeframe)) #Usar timeframe definido

    def mostrar_grafico(self, ventana_actual, divisa, timeframe):
        asyncio.run_coroutine_threadsafe(self.async_mostrar_grafico(ventana_actual, divisa, timeframe), self.loop)

    async def async_mostrar_grafico(self, ventana_actual, divisa, timeframe):
        try:
            data = await self.loop.run_in_executor(self.executor, self.indicadores.obtener_datos, divisa, timeframe, 100)
            if data.empty:
                raise ValueError("No se obtuvieron datos del servidor. Verifica el símbolo y el timeframe.")
            data = await self.loop.run_in_executor(self.executor, self.indicadores.calcular_indicadores, data)
            ultima_hora = data['time'].iloc[-1]
            inicio_ventana = ultima_hora - pd.Timedelta(hours=12)
            data_filtrada = data[data['time'] >= inicio_ventana]

            # Programar la creación del gráfico en el hilo principal de Tkinter
            self.root.after(0, lambda: self.crear_grafico(ventana_actual, divisa, data_filtrada))

        except Exception as e:
            messagebox.showerror("Error", f"Se produjo un error: {str(e)}")

    def crear_grafico(self, ventana_actual, divisa, data_filtrada):
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(data_filtrada['time'], data_filtrada['close'], label="Precio", color='black')
        ax.plot(data_filtrada['time'], data_filtrada['EMA_8'], label="EMA 8", color='orange')
        ax.plot(data_filtrada['time'], data_filtrada['EMA_21'], label="EMA 21", color='green')
        ax.plot(data_filtrada['time'], data_filtrada['EMA_100'], label="EMA 100", color='red')
        ax.text(0.02, 0.95, f"Símbolo: {divisa}", transform=ax.transAxes, fontsize=9, color='blue', backgroundcolor='white', alpha=0.8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.xticks(rotation=45)
        ax.legend()
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=ventana_actual["frame_graficos"])
        canvas.draw()
        ventana_actual["graficos"][divisa] = {"fig": fig, "ax": ax, "canvas": canvas}

        num_graficos = len(ventana_actual["graficos"])
        posiciones = [(0, 0), (0, 1), (1, 0), (1, 1)]

        if num_graficos <= 4:
            fila, columna = posiciones[num_graficos - 1]
            canvas.get_tk_widget().grid(row=fila, column=columna, padx=10, pady=10, sticky="nsew")
            canvas.get_tk_widget().update_idletasks()
        else:
            messagebox.showwarning("Límite alcanzado", "No se pueden agregar más de 4 gráficos en una ventana.")

    def actualizar_grafico(self, ventana_actual, divisa, timeframe):
        asyncio.run_coroutine_threadsafe(self.async_actualizar_grafico(ventana_actual, divisa, timeframe), self.loop)

    async def async_actualizar_grafico(self, ventana_actual, divisa, timeframe):
        try:
            data = await self.loop.run_in_executor(self.executor, self.indicadores.obtener_datos, divisa, timeframe, 100)
            if data.empty:
                raise ValueError("No se obtuvieron datos del servidor. Verifica el símbolo y el timeframe.")
            data = await self.loop.run_in_executor(self.executor, self.indicadores.calcular_indicadores, data)
            ultima_hora = data['time'].iloc[-1]
            inicio_ventana = ultima_hora - pd.Timedelta(hours=12)
            data_filtrada = data[data['time'] >= inicio_ventana]

            # Programar la actualización del gráfico en el hilo principal de Tkinter
            self.root.after(0, lambda: self.actualizar_canvas(ventana_actual, divisa, data_filtrada))

        except Exception as e:
            messagebox.showerror("Error", f"Se produjo un error: {str(e)}")

    def actualizar_canvas(self, ventana_actual, divisa, data_filtrada):
        grafico = ventana_actual["graficos"][divisa]
        ax = grafico["ax"]
        canvas = grafico["canvas"]
        ax.clear()
        ax.plot(data_filtrada['time'], data_filtrada['close'], label="Precio", color='black')
        ax.plot(data_filtrada['time'], data_filtrada['EMA_8'], label="EMA 8", color='orange')
        ax.plot(data_filtrada['time'], data_filtrada['EMA_21'], label="EMA 21", color='green')
        ax.plot(data_filtrada['time'], data_filtrada['EMA_100'], label="EMA 100", color='red')
        ax.text(0.02, 0.95, f"Símbolo: {divisa}", transform=ax.transAxes, fontsize=9, color='blue', backgroundcolor='white', alpha=0.8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.xticks(rotation=45)
        ax.legend()
        plt.tight_layout()
        canvas.draw()

        ultima_senal = data_filtrada['Signal'].iloc[-1]
        signal_change = data_filtrada['Signal_Change'].iloc[-1]

        if signal_change:
            future = asyncio.run_coroutine_threadsafe(
                self.logica.enviar_alerta(ultima_senal, divisa), self.loop
            )
            future.result()

        timeframe = "1H"
        self.root.after(self.intervalo_actualizacion, lambda ventana=ventana_actual, divisa=divisa, timeframe=timeframe: self.actualizar_grafico(ventana, divisa, timeframe))



if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionTrading(root)
    root.mainloop()