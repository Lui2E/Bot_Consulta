import os
import logging
import threading
import requests
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
APIPERU_TOKEN = os.getenv("APIPERU_TOKEN")
APIPERU_URL = "https://apiperu.dev/api/dni/"

# Servidor Flask para mantener vivo el servicio en Render
app = Flask('')

@app.route('/')
def home():
    return "Bot de Consulta DNI está vivo!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Configuración del Bot
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

def consultar_dni_apiperu(dni):
    headers = {"Authorization": f"Bearer {APIPERU_TOKEN}"}
    try:
        response = requests.get(f"{APIPERU_URL}{dni}", headers=headers, timeout=10)
        if response.status_code == 200:
            res = response.json()
            if res.get("success"):
                d = res.get("data")
                return f"✅ **Datos Encontrados:**\n\n👤 {d['nombre_completo']}\n🆔 DNI: {dni}"
        return "❌ No se encontraron datos o error en la API."
    except Exception as e:
        return f"⚠️ Error: {e}"

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(f"Hola {message.from_user.first_name}, envíame un DNI de 8 dígitos.")

@dp.message(F.text.regexp(r"^\d{8}$"))
async def handle_dni(message: Message):
    res = consultar_dni_apiperu(message.text)
    await message.answer(res, parse_mode="Markdown")

async def main():
    # Iniciamos Flask en un hilo separado
    threading.Thread(target=run_flask).start()
    # Iniciamos el Bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
