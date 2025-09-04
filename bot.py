import asyncio
import random
import json
import os
from pyrogram import Client, filters, idle
from pyrogram.types import Message, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup

# Configuración del BOT (REEMPLAZA CON TU TOKEN REAL)
BOT_TOKEN = "8283185863:AAGLW1SlkShUvmk15aZNMRVJ7p9NNIFvcdE"  # ⚠️ REEMPLAZA ESTO

# Configuración de la API
API_ID = 13876032
API_HASH = "c87c88faace9139628f6c7ffc2662bff"

# Variables globales
SESSION_STRING = None
user_client = None
bot_client = None
confirmacion_activa = False
usuario_esperando_confirmacion = None

# Archivo para guardar la sesión
SESSION_FILE = "session_data.json"

def load_session():
    """Cargar sesión desde archivo"""
    global SESSION_STRING
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
                SESSION_STRING = data.get("session_string")
                return True
    except Exception as e:
        print(f"Error cargando sesión: {e}")
    return False

def save_session(session_string):
    """Guardar sesión en archivo"""
    global SESSION_STRING
    SESSION_STRING = session_string
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump({"session_string": session_string}, f)
        return True
    except Exception as e:
        print(f"Error guardando sesión: {e}")
        return False

def initialize_user_client():
    """Inicializar el cliente de usuario de Pyrogram"""
    global user_client
    if SESSION_STRING:
        try:
            user_client = Client(
                "user_account",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=SESSION_STRING,
                in_memory=True
            )
            return True
        except Exception as e:
            print(f"Error inicializando cliente de usuario: {e}")
    return False

def initialize_bot_client():
    """Inicializar el cliente bot de Pyrogram"""
    global bot_client
    try:
        bot_client = Client(
            "bot_account",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            in_memory=True
        )
        return True
    except Exception as e:
        print(f"Error inicializando bot client: {e}")
        return False

def generate_random_name():
    """Genera nombre aleatorio para grupo"""
    adjectives = ["Grande", "Pequeño", "Rápido", "Lento", "Inteligente", "Divertido", "Activo", "Popular"]
    nouns = ["Grupo", "Chat", "Comunidad", "Club", "Equipo", "Proyecto", "Canal", "Foro"]
    return f"{random.choice(adjectives)} {random.choice(nouns)} {random.randint(1000, 9999)}"

async def crear_grupos(message: Message):
    """Función que crea los grupos"""
    try:
        if not user_client or not user_client.is_connected:
            await message.reply("❌ Cliente de usuario no conectado")
            return
            
        progress_msg = await message.reply("🔄 Creando 50 grupos...\n\n0/50 completados")
        
        grupos_creados = 0
        grupos_fallidos = 0
        resultados = []

        for i in range(1, 51):
            try:
                # Crear supergrupo
                group_name = generate_random_name()
                group = await user_client.create_supergroup(
                    title=group_name,
                    description=f"Grupo automático #{i}"
                )

                grupos_creados += 1
                resultados.append(f"✅ Grupo {i}: {group_name}")
                
                # Actualizar progreso cada 5 grupos
                if i % 5 == 0:
                    await progress_msg.edit_text(
                        f"🔄 Creando grupos...\n\n{i}/50 completados\n"
                        f"✅ Éxitos: {grupos_creados}\n"
                        f"❌ Fallos: {grupos_fallidos}"
                    )

                await asyncio.sleep(5)

            except Exception as e:
                grupos_fallidos += 1
                error_msg = str(e)
                if "FLOOD" in error_msg.upper():
                    error_msg = "Límite de flood - espera"
                resultados.append(f"❌ Grupo {i}: {error_msg}")
                await asyncio.sleep(10)

        # Resultado final
        await message.reply(
            f"🎉 **Proceso completado!**\n\n"
            f"✅ Grupos creados: {grupos_creados}\n"
            f"❌ Grupos fallidos: {grupos_fallidos}"
        )
        
        # Enviar resumen en chunks
        chunk_size = 10
        for i in range(0, len(resultados), chunk_size):
            chunk = resultados[i:i + chunk_size]
            await message.reply("\n".join(chunk))
            await asyncio.sleep(2)

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

async def restart_user_client():
    """Reiniciar el cliente de usuario"""
    global user_client
    if user_client and user_client.is_connected:
        await user_client.stop()
    
    if initialize_user_client():
        await user_client.start()
        print("✅ Cliente de usuario reiniciado")
    else:
        print("❌ Error reiniciando cliente")

# Función para registrar los handlers después de inicializar el bot
def register_handlers():
    """Registrar todos los handlers después de inicializar el bot"""
    
    @bot_client.on_message(filters.command("set") & filters.private)
    async def set_session_command(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply("❌ Uso: /set <session_string>")
            return
        
        session_string = message.command[1]
        if save_session(session_string):
            await message.reply("✅ Sesión guardada. Reconectando...")
            await restart_user_client()
        else:
            await message.reply("❌ Error guardando sesión")

    @bot_client.on_message(filters.command("creargrupos") & filters.private)
    async def crear_grupos_command(client: Client, message: Message):
        global confirmacion_activa, usuario_esperando_confirmacion
        
        if not SESSION_STRING:
            await message.reply("❌ Configura una sesión con /set <session_string>")
            return
        
        try:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ SI", callback_data="confirm_yes")],
                [InlineKeyboardButton("❌ NO", callback_data="confirm_no")]
            ])
            
            await message.reply(
                "⚠️ **ADVERTENCIA** ⚠️\n\n"
                "Vas a crear 50 grupos. Esto puede:\n"
                "• Ser detectado como spam\n"
                "• Causar limitaciones temporales\n\n"
                "¿Continuar?",
                reply_markup=keyboard
            )
            
            confirmacion_activa = True
            usuario_esperando_confirmacion = message.from_user.id
            
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")

    @bot_client.on_callback_query()
    async def handle_callbacks(client: Client, callback_query):
        global confirmacion_activa, usuario_esperando_confirmacion
        
        if callback_query.from_user.id != usuario_esperando_confirmacion:
            await callback_query.answer("❌ No es para ti")
            return
        
        if callback_query.data == "confirm_yes":
            confirmacion_activa = False
            usuario_esperando_confirmacion = None
            await callback_query.message.edit("✅ Confirmado. Iniciando...")
            await crear_grupos(callback_query.message)
        elif callback_query.data == "confirm_no":
            confirmacion_activa = False
            usuario_esperando_confirmacion = None
            await callback_query.message.edit("❌ Cancelado.")
        
        await callback_query.answer()

    @bot_client.on_message(filters.command("start") & filters.private)
    async def start_command(client: Client, message: Message):
        if not SESSION_STRING:
            await message.reply(
                "🤖 **Bot Creador de Grupos**\n\n"
                "⚠️ Configura una sesión primero:\n"
                "/set <session_string>\n\n"
                "Para obtener session_string:\n"
                "1. Visita https://replit.com/@ayrahikari/pyrogram-session-string\n"
                "2. Genera tu session_string\n"
                "3. Usa /set <codigo>"
            )
        else:
            await message.reply(
                "🤖 **Bot Creador de Grupos**\n\n"
                "✅ Sesión configurada\n\n"
                "Comandos:\n"
                "/creargrupos - Crear 50 grupos\n"
                "/test - Probar con 2 grupos\n"
                "/estado - Ver estado\n"
                "/setsession - Cambiar sesión"
            )

    @bot_client.on_message(filters.command("test") & filters.private)
    async def test_command(client: Client, message: Message):
        if not SESSION_STRING:
            await message.reply("❌ Configura una sesión con /set")
            return
        
        try:
            await message.reply("🧪 Probando con 2 grupos...")
            grupos_test_creados = 0
            
            for i in range(1, 3):
                try:
                    group_name = generate_random_name()
                    group = await user_client.create_supergroup(
                        title=group_name,
                        description=f"Grupo prueba #{i}"
                    )
                    grupos_test_creados += 1
                    await message.reply(f"✅ Grupo {i}: {group_name}")
                    await asyncio.sleep(3)
                except Exception as e:
                    error_msg = "Límite de flood" if "FLOOD" in str(e).upper() else str(e)
                    await message.reply(f"❌ Error {i}: {error_msg}")
                    break
            
            await message.reply(f"🧪 Prueba: {grupos_test_creados}/2 grupos")
                    
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")

    @bot_client.on_message(filters.command("estado") & filters.private)
    async def estado_command(client: Client, message: Message):
        status = "✅ Configurada\n" if SESSION_STRING else "❌ No configurada\n"
        user_conn = "✅ Conectado\n" if user_client and user_client.is_connected else "❌ Desconectado\n"
        bot_conn = "✅ Conectado\n" if bot_client and bot_client.is_connected else "❌ Desconectado\n"
        
        await message.reply(
            f"🤖 **Estado:**\n\n"
            f"**Sesión:** {status}"
            f"**Usuario:** {user_conn}"
            f"**Bot:** {bot_conn}"
        )

    @bot_client.on_message(filters.command("setsession") & filters.private)
    async def change_session_command(client: Client, message: Message):
        await message.reply(
            "🔄 Para cambiar sesión:\n\n"
            "1. Visita https://replit.com/@ayrahikari/pyrogram-session-string\n"
            "2. Genera nueva session_string\n"
            "3. Usa /set <nuevo_codigo>"
        )

# Función principal
async def main():
    # Verificar token primero
    if BOT_TOKEN == "TU_BOT_TOKEN_AQUI":
        print("❌ ERROR: Debes reemplazar BOT_TOKEN con tu token real de @BotFather")
        return
    
    # Cargar sesión existente
    load_session()
    
    # Inicializar bot primero
    if not initialize_bot_client():
        print("❌ Error: No se pudo inicializar el bot")
        return
    
    try:
        # Iniciar bot
        await bot_client.start()
        print("✅ Bot iniciado correctamente")
        
        # Registrar handlers DESPUÉS de iniciar el bot
        register_handlers()
        
        # Inicializar cliente de usuario si hay sesión
        if SESSION_STRING:
            if initialize_user_client():
                await user_client.start()
                print("✅ Cliente de usuario iniciado")
        
        # Mostrar información del bot
        me = await bot_client.get_me()
        print(f"🤖 Bot: @{me.username}")
        print("📱 Envía /start a tu bot")
        
        # Mantener el bot corriendo
        await idle()
        
    except Exception as e:
        print(f"❌ Error en main: {e}")
    finally:
        # Cerrar conexiones
        if user_client and user_client.is_connected:
            await user_client.stop()
        if bot_client and bot_client.is_connected:
            await bot_client.stop()

if __name__ == "__main__":
    # Crear archivo de sesión si no existe
    if not os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'w') as f:
                json.dump({"session_string": None}, f)
        except:
            pass
    
    print("🤖 Iniciando Bot Creador de Grupos...")
    
    # Ejecutar el bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot detenido por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando: {e}")
