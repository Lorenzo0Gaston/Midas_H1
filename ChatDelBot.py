from telegram import Bot

# Token del bot y chat_id
TOKEN = "TOKEN"
CHAT_ID = "Chat ID"

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
