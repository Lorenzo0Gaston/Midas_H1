import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import pandas as pd
import asyncio
import threading
from Logica import Logica
from Indicador import Indicadores

class AplicacionTrading:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplicación de Trading")
        self.indicadores = Indicadores()
        self.logica = Logica(self.root)

        # Lista de divisas disponibles
        self.divisas = ["XAUUSD", "AUDUSD", "USDCAD", "EURUSD", "GBPUSD",
                        "USDOIL", "USDJPY", "NZDUSD", "GBPCHF", "US30", "US500M"]

        # Elementos de la GUI
        self.frame_ordenes = tk.Frame(root)
        self.frame_ordenes.pack(side=tk.LEFT, padx=10)

        self.label_simbolo = tk.Label(self.frame_ordenes, text="Seleccionar divisas:")
        self.label_simbolo.grid(row=0, column=0)

        self.combo_divisas = ttk.Combobox(self.frame_ordenes, values=self.divisas)
        self.combo_divisas.grid(row=0, column=1)
        self.combo_divisas.set("XAUUSD")  # Valor predeterminado

        self.label_timeframe = tk.Label(self.frame_ordenes, text="Timeframe:")
        self.label_timeframe.grid(row=1, column=0)

        self.combo_timeframe = ttk.Combobox(
            self.frame_ordenes, values=["1H", "4H", "1D"])
        self.combo_timeframe.grid(row=1, column=1)
        self.combo_timeframe.set("1H")  # Valor predeterminado

        self.boton_graficar = tk.Button(
            self.frame_ordenes, text="Añadir Gráfico", command=self.añadir_grafico)
        self.boton_graficar.grid(row=2, column=0, columnspan=2)

        # Lista para almacenar las ventanas y gráficos abiertos
        self.ventanas_graficos = []

        # Tamaño fijo para las ventanas de gráficos
        self.ventana_ancho = 1200  # Ancho de la ventana
        self.ventana_alto = 800    # Alto de la ventana

        # Intervalo de actualización en milisegundos (por ejemplo, 5000 ms = 5 segundos)
        self.intervalo_actualizacion = 5000

        # Iniciar el bucle de eventos de asyncio en un hilo separado
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_loop, args=(self.loop,), daemon=True).start()

    def start_loop(self, loop):
        """Iniciar el bucle de eventos de asyncio en un hilo separado."""
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def añadir_grafico(self):
        """Añade un nuevo gráfico en una ventana."""
        divisa = self.combo_divisas.get()
        timeframe = self.combo_timeframe.get()

        # Verificar si la divisa ya está siendo mostrada
        for ventana in self.ventanas_graficos:
            if divisa in ventana["divisas"]:
                messagebox.showwarning("Advertencia", f"La divisa {divisa} ya está siendo mostrada.")
                return

        # Crear una nueva ventana si no hay espacio en las ventanas existentes
        if not self.ventanas_graficos or len(self.ventanas_graficos[-1]["divisas"]) >= 4:
            nueva_ventana = tk.Toplevel(self.root)
            nueva_ventana.title("Gráficos de Trading")
            
            # Establecer el tamaño fijo de la ventana
            nueva_ventana.geometry(f"{self.ventana_ancho}x{self.ventana_alto}")
            
            frame_graficos = tk.Frame(nueva_ventana)
            frame_graficos.pack()

            self.ventanas_graficos.append({
                "ventana": nueva_ventana,
                "frame_graficos": frame_graficos,
                "divisas": [],
                "graficos": {}  # Diccionario para almacenar los gráficos por divisa
            })

        # Añadir el gráfico a la última ventana creada
        ventana_actual = self.ventanas_graficos[-1]
        ventana_actual["divisas"].append(divisa)
        self.mostrar_grafico(ventana_actual, divisa, timeframe)

        # Programar la actualización del gráfico
        self.root.after(self.intervalo_actualizacion, lambda: self.actualizar_grafico(ventana_actual, divisa, timeframe))

    def mostrar_grafico(self, ventana_actual, divisa, timeframe):
        """Muestra un gráfico en el frame especificado."""
        try:
            # Obtener datos del mercado
            data = self.indicadores.obtener_datos(divisa, timeframe, 100)
            if data.empty:
                raise ValueError("No se obtuvieron datos del servidor. Verifica el símbolo y el timeframe.")

            # Calcular indicadores
            print("Calculando indicadores...")  # Debug
            data = self.indicadores.calcular_indicadores(data)
            print("Indicadores calculados correctamente.")  # Debug

            # Filtrar los datos para mostrar solo las últimas 12 horas
            ultima_hora = data['time'].iloc[-1]  # Última hora en los datos
            inicio_ventana = ultima_hora - pd.Timedelta(hours=12)  # Hace 12 horas desde la última hora
            data_filtrada = data[data['time'] >= inicio_ventana]  # Filtrar datos

            # Crear una nueva figura y ejes
            fig, ax = plt.subplots(figsize=(6, 3))  # Tamaño más pequeño para 4 gráficos por ventana

            # Dibujar el gráfico
            ax.plot(data_filtrada['time'], data_filtrada['close'], label="Precio", color='black')
            ax.plot(data_filtrada['time'], data_filtrada['EMA_8'], label="EMA 8", color='orange')
            ax.plot(data_filtrada['time'], data_filtrada['EMA_21'], label="EMA 21", color='green')
            ax.plot(data_filtrada['time'], data_filtrada['EMA_100'], label="EMA 100", color='red')

            # Agregar el símbolo de la divisa en el gráfico
            ax.text(
                0.02, 0.95, f"Símbolo: {divisa}", transform=ax.transAxes,
                fontsize=9, color='blue', backgroundcolor='white', alpha=0.8
            )

            # Formatear el eje x para mostrar horas
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))

            # Rotar etiquetas del eje x
            plt.xticks(rotation=45)

            # Añadir leyenda
            ax.legend()
            plt.tight_layout()

            # Crear el canvas y empaquetarlo en el frame
            canvas = FigureCanvasTkAgg(fig, master=ventana_actual["frame_graficos"])
            canvas.draw()

            # Almacenar el gráfico en el diccionario de la ventana
            ventana_actual["graficos"][divisa] = {
                "fig": fig,
                "ax": ax,
                "canvas": canvas
            }

            # 📌 Contar gráficos existentes en la ventana
            num_graficos = len(ventana_actual["frame_graficos"].grid_slaves())  # Obtiene cuántos widgets hay en la grilla
            
            # 📌 Definir posiciones dentro de una matriz 2x2
            posiciones = [(0, 0), (0, 1), (1, 0), (1, 1)]
            
            if num_graficos < 4:  # Solo agregamos hasta 4 gráficos por ventana
                fila, columna = posiciones[num_graficos]
                canvas.get_tk_widget().grid(row=fila, column=columna, padx=10, pady=10, sticky="nsew")
            else:
                messagebox.showwarning("Límite alcanzado", "No se pueden agregar más de 4 gráficos en una ventana.")

            # Asegurar que el frame_graficos expanda correctamente
            ventana_actual["frame_graficos"].grid_rowconfigure(0, weight=1)
            ventana_actual["frame_graficos"].grid_rowconfigure(1, weight=1)
            ventana_actual["frame_graficos"].grid_columnconfigure(0, weight=1)
            ventana_actual["frame_graficos"].grid_columnconfigure(1, weight=1)

        except Exception as e:
            messagebox.showerror("Error", f"Se produjo un error: {str(e)}")

    def actualizar_grafico(self, ventana_actual, divisa, timeframe):
        """Actualiza el gráfico con nuevos datos."""
        try:
            # Obtener datos actualizados del mercado
            data = self.indicadores.obtener_datos(divisa, timeframe, 100)
            if data.empty:
                raise ValueError("No se obtuvieron datos del servidor. Verifica el símbolo y el timeframe.")

            # Calcular indicadores
            data = self.indicadores.calcular_indicadores(data)

            # Filtrar los datos para mostrar solo las últimas 12 horas
            ultima_hora = data['time'].iloc[-1]  # Última hora en los datos
            inicio_ventana = ultima_hora - pd.Timedelta(hours=12)  # Hace 12 horas desde la última hora
            data_filtrada = data[data['time'] >= inicio_ventana]  # Filtrar datos

            # Obtener el gráfico existente
            grafico = ventana_actual["graficos"][divisa]
            ax = grafico["ax"]
            canvas = grafico["canvas"]

            # Limpiar el eje antes de volver a dibujar
            ax.clear()

            # Dibujar el gráfico actualizado
            ax.plot(data_filtrada['time'], data_filtrada['close'], label="Precio", color='black')
            ax.plot(data_filtrada['time'], data_filtrada['EMA_8'], label="EMA 8", color='orange')
            ax.plot(data_filtrada['time'], data_filtrada['EMA_21'], label="EMA 21", color='green')
            ax.plot(data_filtrada['time'], data_filtrada['EMA_100'], label="EMA 100", color='red')

            # Agregar el símbolo de la divisa en el gráfico
            ax.text(
                0.02, 0.95, f"Símbolo: {divisa}", transform=ax.transAxes,
                fontsize=9, color='blue', backgroundcolor='white', alpha=0.8
            )

            # Formatear el eje x para mostrar horas
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))

            # Rotar etiquetas del eje x
            plt.xticks(rotation=45)

            # Añadir leyenda
            ax.legend()
            plt.tight_layout()

            # Redibujar el canvas
            canvas.draw()

            # Verificar si hay un cruce de indicadores
            ultima_senal = data['Signal'].iloc[-1]
            signal_change = data['Signal_Change'].iloc[-1]

            if signal_change:
                # Ejecutar la corrutina en el bucle de eventos de asyncio
                future = asyncio.run_coroutine_threadsafe(
                    self.logica.enviar_alerta(ultima_senal, divisa), self.loop
                )
                # Manejar el futuro para evitar advertencias
                future.result()  # Esto espera a que la corrutina termine

            # Programar la próxima actualización
            self.root.after(self.intervalo_actualizacion, lambda: self.actualizar_grafico(ventana_actual, divisa, timeframe))

        except Exception as e:
            messagebox.showerror("Error", f"Se produjo un error: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionTrading(root)
    root.mainloop()