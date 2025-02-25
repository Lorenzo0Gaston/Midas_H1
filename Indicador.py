import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pytz  # Necesitas instalar pytz: pip install pytz

class Indicadores:
    def __init__(self):
        # Inicializar MetaTrader 5
        if not mt5.initialize():
            print("Error al inicializar MetaTrader 5. Verifica la conexión.")
            quit()

    def obtener_datos(self, simbolo, intervalo, horas=12):
        """Obtiene los datos históricos de las últimas 12 horas."""
        timeframe_dict = {
            "1H": mt5.TIMEFRAME_H1,  # 1 hora
            "4H": mt5.TIMEFRAME_H4,  # 4 horas
            "1D": mt5.TIMEFRAME_D1,  # 1 día (24 horas)
        }

        if intervalo not in timeframe_dict:
            raise ValueError(f"El intervalo '{intervalo}' no es soportado. Usa uno de: {list(timeframe_dict.keys())}")

        # Calcular el número de velas necesarias para las últimas 12 horas
        if intervalo == "1H":
            n_candles = horas  # 12 velas para 12 horas
        elif intervalo == "4H":
            n_candles = horas // 4  # 3 velas para 12 horas
        elif intervalo == "1D":
            n_candles = 1  # 1 vela para 12 horas (redondeo)

        try:
            # Obtener la hora actual en UTC
            ahora = datetime.now(pytz.utc)

            # Calcular la hora de inicio (hace 12 horas)
            inicio = ahora - timedelta(hours=horas)

            # Obtener datos históricos desde la hora de inicio
            rates = mt5.copy_rates_from(simbolo, timeframe_dict[intervalo], inicio, n_candles)
            if rates is None:
                raise ValueError(f"No se obtuvieron datos para el símbolo {simbolo} y timeframe {intervalo}.")

            # Convertir a DataFrame
            data = pd.DataFrame(rates)
            data['time'] = pd.to_datetime(data['time'], unit='s')

            # Convertir la hora a UTC-5 (Horario de Nueva York)
            data['time'] = data['time'].dt.tz_localize('UTC').dt.tz_convert('America/New_York')

            return data

        except Exception as e:
            print(f"Error al obtener datos: {e}")
            return pd.DataFrame()  # Retornar un DataFrame vacío en caso de error

    def calcular_indicadores(self, data):
        """Calcula indicadores como EMA y señales de compra/venta."""
        if data.empty:
            raise ValueError("El dataframe está vacío. No se pueden calcular indicadores.")

        # Calcular las EMAs
        data['EMA_8'] = data['close'].ewm(span=8).mean()
        data['EMA_21'] = data['close'].ewm(span=21).mean()
        data['EMA_100'] = data['close'].ewm(span=100).mean()  # Nueva EMA 100

        # Determinar la señal actual
        data['Signal'] = np.where(data['EMA_8'] > data['EMA_21'], 'compra', 'venta')

        # Detectar cambios en la señal
        data['Signal_Change'] = data['Signal'].ne(data['Signal'].shift())

        return data