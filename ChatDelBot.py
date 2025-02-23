from telegram import Bot

# Token del bot y chat_id
TOKEN = "7975954346:AAGZml5vbuT5cTt6d2i9z11MvqoltEHfbWM"
CHAT_ID = "-4731258133"

async def send_message():
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text="Este es un mensaje de prueba.")
        print("Mensaje enviado correctamente.")
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

# Ejecutar la función asíncrona
if __name__ == "__main__":
    import asyncio
    asyncio.run(send_message())