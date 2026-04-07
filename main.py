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
# TIP: Obtén tu ID con el bot @userinfobot en Telegram y ponlo aquí o en Render como variable de entorno
ADMIN_ID = os.getenv("ADMIN_ID") 

# Servidor Flask para mantener vivo el servicio en Render
app = Flask('')

@app.route('/')
def home():
    return "Bot de Consulta DNI está vivo!"

def run_flask():
    # Render usa el puerto 8080 por defecto para Web Services
    app.run(host='0.0.0.0', port=8080)

# Configuración de Logging
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
                return {
                    "status": True,
                    "msg": f"✅ **Datos Encontrados:**\n\n👤 {d['nombre_completo']}\n🆔 DNI: {dni}",
                    "nombre": d['nombre_completo']
                }
        return {"status": False, "msg": "❌ No se encontraron datos o error en la API."}
    except Exception as e:
        return {"status": False, "msg": f"⚠️ Error: {e}"}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(f"Hola {message.from_user.first_name}, envíame un DNI de 8 dígitos para consultar.")

@dp.message(F.text.regexp(r"^\d{8}$"))
async def handle_dni(message: Message):
    dni = message.text
    user = message.from_user
    
    # 1. Registro en Logs de Render
    print(f"--- CONSULTA RECIBIDA ---")
    print(f"Usuario: {user.full_name} (@{user.username})")
    print(f"ID: {user.id}")
    print(f"DNI: {dni}")
    print(f"-------------------------")

    # Realizar consulta
    resultado = consultar_dni_apiperu(dni)
    await message.answer(resultado["msg"], parse_mode="Markdown")

    # 2. Notificación al Administrador (Opcional)
    if ADMIN_ID:
        try:
            info_admin = f"🔔 **Nueva Consulta**\n👤 De: {user.full_name}\n🆔 DNI buscado: {dni}"
            if resultado["status"]:
                info_admin += f"\n📄 Resultado: {resultado['nombre']}"
            
            await bot.send_message(chat_id=ADMIN_ID, text=info_admin)
        except Exception as e:
            print(f"Error enviando notificación al admin: {e}")

async def main():
    # Iniciamos Flask en un hilo separado para que no bloquee al bot
    threading.Thread(target=run_flask, daemon=True).start()
    # Iniciamos el Bot con polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
