import pandas as pd
import numpy as np
import MetaTrader5 as mt5

class Indicadores:
    def __init__(self):
        # Inicializar MetaTrader 5
        if not mt5.initialize():
            print("Error al inicializar MetaTrader 5. Verifica la conexión.")
            quit()

    def obtener_datos(self, simbolo, intervalo, n_candles):
        timeframe_dict = {
            "1H": mt5.TIMEFRAME_H1,  # 1 hora
            "4H": mt5.TIMEFRAME_H4,  # 4 horas
            "1D": mt5.TIMEFRAME_D1,  # 1 día (24 horas)
        }

        if intervalo not in timeframe_dict:
            raise ValueError(f"El intervalo '{intervalo}' no es soportado. Usa uno de: {list(timeframe_dict.keys())}")

        try:
            # Obtener datos históricos
            rates = mt5.copy_rates_from_pos(simbolo, timeframe_dict[intervalo], 0, n_candles)
            if rates is None:
                raise ValueError(f"No se obtuvieron datos para el símbolo {simbolo} y timeframe {intervalo}.")

            # Convertir a DataFrame
            data = pd.DataFrame(rates)
            data['time'] = pd.to_datetime(data['time'], unit='s')
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