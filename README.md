Las manos de Midas:
La GUI toma los parametros con los que va a trabajar, los mismos son ingresados manualmente para que trabaje.
Logica: es el bacend de la GUI para que funcione.
Indicaddor: script tomado de pine script, a travez de los cruces de colores (verde y rojo)
Avisos: momentos antes del cruze de los colores, debe enviar un mensaje a travez de ttelegram notificando
    que se aproxima al momenton de hacer una entrada, para realizar la entrada de forma manual. 
    Es una ayuda para optimizar las ganancias, pero debe ser controladado
En este proyecto, "Midas_H1" es un programa el cual se conecta a MetaTrader5 para obtener datos en tiempo real, con una actualizacion de cada 5 segundos. 
Los mismos los procesa y grafica en una ventana nueva a cada divisa ingresada.
Ademas de agregar los indicadores de EMA's en los cuales se muesta la tendencia en la bolsa, y mediante otros 2 indicadores y por mensaje de telegram a 
  un bot da alerta de comprar o vender dicha divisa. Por otra parte en una carpeta dentro de la maquina donde se ejecuta el programa guarda los graficos 
  indicando la divisa la fecha y hora en que se dio el alerta.

Un programa sensillo medianamente efectivo ya que esta sujeto a valores no controlados, aletorios, y de volatilidad del mercado o no, dependiendo de situaciones geopoliticas
