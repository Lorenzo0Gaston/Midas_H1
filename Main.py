import Logica
import MetaTrader5 as mt5

# Inicializar MetaTrader5
mt5.initialize()

# Código para iniciar el trading en tiempo real
logica = Logica.Logica()
logica.ejecutar_trading_en_tiempo_real("XAUUSD", mt5.TIMEFRAME_M5, 0.1, 10, 20)  # Ejemplo de uso