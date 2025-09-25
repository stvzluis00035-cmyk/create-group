import asyncio
import random
import json
import os
import datetime
from pyrogram import Client, filters, idle
from pyrogram.types import Message, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import SessionPasswordNeeded, PhoneNumberInvalid, PhoneCodeInvalid
from collections import defaultdict

# Configuración del BOT (REEMPLAZA CON TU TOKEN REAL)
BOT_TOKEN = "7559435897:AAEZRmZ7ejeQUnwgh1S-KifQNyaTgqLYtR0"  # ⚠️ REEMPLAZA ESTO

# Configuración de la API
API_ID = 13876032
API_HASH = "c87c88faace9139628f6c7ffc2662bff"

# Variables globales
user_client = None
bot_client = None

# Estructuras para manejar múltiples usuarios
user_sessions = defaultdict(dict)  # {user_id: {"session_string": "", "client": None, "active": False, "user_name": ""}}
confirmaciones_activas = {}  # {user_id: True/False}
login_states = {}  # {user_id: {"step": "phone", "phone_code_hash": "", "client": None}}
language_selection = {}  # {user_id: {"language": "", "step": "awaiting_selection"}}

# Archivo para guardar las sesiones de usuarios
SESSIONS_FILE = "user_sessions.json"

# Diccionarios de palabras por idioma
WORDS = {
    "español": [
        "jugar", "caminar", "hola", "cómo", "estás", "bien", "casa", "mesa",
        "perro", "gato", "sol", "luna", "agua", "fuego", "aire", "tierra",
        "libro", "pluma", "silla", "puerta", "ventana", "comida", "bebida", "amigo",
        "familia", "trabajo", "escuela", "ciudad", "campo", "flor", "árbol", "rio",
        "mar", "montaña", "playa", "cielo", "nube", "estrella", "tiempo", "reloj",
        "dinero", "ropa", "zapato", "sombrero", "color", "música", "arte", "deporte",
        "juego", "feliz", "triste", "enojado", "calor", "frío", "dulce", "salado",
        "rápido", "lento", "grande", "pequeño", "nuevo", "viejo", "bueno", "malo",
        "fácil", "difícil", "primero", "último", "derecha", "izquierda", "arriba", "abajo",
        "dentro", "fuera", "lejos", "cerca", "siempre", "nunca", "ahora", "después"
    ],
    "ingles": [
        "play", "walk", "hello", "how", "are", "good", "house", "table",
        "dog", "cat", "sun", "moon", "water", "fire", "air", "earth",
        "book", "pen", "chair", "door", "window", "food", "drink", "friend",
        "family", "work", "school", "city", "field", "flower", "tree", "river",
        "sea", "mountain", "beach", "sky", "cloud", "star", "time", "clock",
        "money", "clothes", "shoe", "hat", "color", "music", "art", "sport",
        "game", "happy", "sad", "angry", "hot", "cold", "sweet", "salty",
        "fast", "slow", "big", "small", "new", "old", "good", "bad",
        "easy", "hard", "first", "last", "right", "left", "up", "down",
        "inside", "outside", "far", "near", "always", "never", "now", "later"
    ],
    "ruso": [
        "играть", "ходить", "привет", "как", "ты", "хорошо", "дом", "стол",
        "собака", "кошка", "солнце", "луна", "вода", "огонь", "воздух", "земля",
        "книга", "ручка", "стул", "дверь", "окно", "еда", "пить", "друг",
        "семья", "работа", "школа", "город", "поле", "цветок", "дерево", "река",
        "море", "гора", "пляж", "небо", "облако", "звезда", "время", "часы",
        "деньги", "одежда", "обувь", "шляпа", "цвет", "музыка", "искусство", "спорт",
        "игра", "счастливый", "грустный", "сердитый", "горячий", "холодный", "сладкий", "соленый",
        "быстро", "медленно", "большой", "маленький", "новый", "старый", "хороший", "плохой",
        "легко", "трудно", "первый", "последний", "правый", "левый", "вверх", "вниз",
        "внутри", "снаружи", "далеко", "близко", "всегда", "никогда", "сейчас", "позже"
    ],
    "árabe": [
        "يلعب", "يمشي", "مرحبا", "كيف", "أنت", "جيد", "بيت", "طاولة",
        "كلب", "قطة", "شمس", "قمر", "ماء", "نار", "هواء", "أرض",
        "كتاب", "قلم", "كرسي", "باب", "نافذة", "طعام", "شراب", "صديق",
        "عائلة", "عمل", "مدرسة", "مدينة", "حقل", "زهرة", "شجرة", "نهر",
        "بحر", "جبل", "شاطئ", "سماء", "سحابة", "نجمة", "وقت", "ساعة",
        "مال", "ملابس", "حذاء", "قبعة", "لون", "موسيقى", "فن", "رياضة",
        "لعبة", "سعيد", "حزين", "غاضب", "حار", "بارد", "حلو", "مالح",
        "سريع", "بطيء", "كبير", "صغير", "جديد", "قديم", "جيد", "سيء",
        "سهل", "صعب", "أول", "آخر", "يمين", "يسار", "أعلى", "أسفل",
        "داخل", "خارج", "بعيد", "قريب", "دائما", "أبدا", "الآن", "بعد"
    ]
}

def load_sessions():
    """Cargar sesiones de usuarios desde archivo"""
    global user_sessions
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'r') as f:
                data = json.load(f)
                for user_id, session_data in data.items():
                    user_sessions[int(user_id)] = session_data
                return True
    except Exception as e:
        print(f"Error cargando sesiones: {e}")
    return False

def save_sessions():
    """Guardar sesiones de usuarios en archivo"""
    try:
        # Convertir a formato serializable
        serializable_sessions = {}
        for user_id, session_data in user_sessions.items():
            serializable_sessions[str(user_id)] = {
                "session_string": session_data.get("session_string"),
                "active": session_data.get("active", False),
                "user_name": session_data.get("user_name", "")
            }
        
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(serializable_sessions, f)
        return True
    except Exception as e:
        print(f"Error guardando sesiones: {e}")
        return False

async def initialize_user_client(user_id):
    """Inicializar el cliente de usuario de Pyrogram para un usuario específico"""
    session_data = user_sessions.get(user_id, {})
    session_string = session_data.get("session_string")
    
    if not session_string:
        return False
        
    try:
        # Si ya existe un cliente, detenerlo primero
        if "client" in user_sessions[user_id] and user_sessions[user_id]["client"] and user_sessions[user_id]["client"].is_connected:
            await user_sessions[user_id]["client"].stop()
            
        # Crear nuevo cliente
        user_client = Client(
            f"user_account_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True
        )
        
        user_sessions[user_id]["client"] = user_client
        await user_client.start()
        user_sessions[user_id]["active"] = True
        
        # Obtener información del usuario (incluyendo nombre)
        try:
            me = await user_client.get_me()
            user_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
            if not user_name:
                user_name = f"Usuario {user_id}"
            user_sessions[user_id]["user_name"] = user_name
            print(f"✅ Usuario {user_id} - {user_name} conectado")
        except Exception as e:
            print(f"⚠️ Error obteniendo info del usuario {user_id}: {e}")
            user_sessions[user_id]["user_name"] = f"Usuario {user_id}"
            
        return True
    except Exception as e:
        print(f"Error inicializando cliente de usuario {user_id}: {e}")
        user_sessions[user_id]["active"] = False
        user_sessions[user_id]["user_name"] = f"Usuario {user_id}"
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

async def enviar_mensajes_aleatorios(client, group_id, language):
    """Envía 8 mensajes con palabras aleatorias al grupo (sin username)"""
    try:
        palabras_disponibles = WORDS[language].copy()
        random.shuffle(palabras_disponibles)
        
        for i in range(8):
            if not palabras_disponibles:
                # Si se acaban las palabras, regenerar la lista
                palabras_disponibles = WORDS[language].copy()
                random.shuffle(palabras_disponibles)
            
            # Tomar entre 1-3 palabras para cada mensaje
            num_palabras = random.randint(1, 3)
            palabras_mensaje = []
            
            for _ in range(num_palabras):
                if palabras_disponibles:
                    palabras_mensaje.append(palabras_disponibles.pop())
            
            mensaje = " ".join(palabras_mensaje)
            await client.send_message(group_id, mensaje)
            
            # Espera aleatoria entre mensajes (1-3 segundos)
            await asyncio.sleep(random.uniform(1, 3))
        
        return True
    except Exception as e:
        print(f"Error enviando mensajes aleatorios: {e}")
        return False

async def crear_grupos(message: Message, user_id, language):
    """Función que crea los grupos para un usuario específico en el idioma seleccionado"""
    try:
        user_data = user_sessions.get(user_id, {})
        if not user_data or "client" not in user_data or not user_data["client"].is_connected:
            await message.reply("❌ Cliente de usuario no conectado. Usa /set primero.")
            return
            
        client = user_data["client"]
        user_name = user_data.get("user_name", f"Usuario {user_id}")
        
        progress_msg = await message.reply(f"🔄 Creando 50 grupos en {language} con sesión {user_name}...\n\n0/50 completados")
        
        grupos_creados = 0
        grupos_fallidos = 0
        resultados = []

        for i in range(1, 51):
            try:
                # Crear supergrupo
                group_name = generate_random_name()
                group = await client.create_supergroup(
                    title=group_name,
                    description=f"Grupo automático #{i} - Sesión: {user_name}"
                )

                # Obtener ID del grupo
                group_id = group.id
                
                # Enviar mensajes aleatorios al grupo (sin username)
                mensajes_enviados = await enviar_mensajes_aleatorios(client, group_id, language)
                
                grupos_creados += 1
                resultado = f"✅ Grupo {i}: {group_name} (Sesión: {user_name})"
                if not mensajes_enviados:
                    resultado += " (error enviando mensajes)"
                resultados.append(resultado)
                
                # Actualizar progreso cada 5 grupos
                if i % 5 == 0:
                    await progress_msg.edit_text(
                        f"🔄 Creando grupos en {language} con sesión {user_name}...\n\n{i}/50 completados\n"
                        f"✅ Éxitos: {grupos_creados}\n"
                        f"❌ Fallos: {grupos_fallidos}"
                    )

                # Espera entre grupos (3-7 segundos)
                await asyncio.sleep(random.uniform(3, 7))

            except Exception as e:
                grupos_fallidos += 1
                error_msg = str(e)
                if "FLOOD" in error_msg.upper():
                    error_msg = "Límite de flood - espera"
                    # Espera más larga por flood
                    await asyncio.sleep(30)
                else:
                    await asyncio.sleep(10)
                
                resultados.append(f"❌ Grupo {i}: {error_msg} (Sesión: {user_name})")

        # Resultado final
        await message.reply(
            f"🎉 **Proceso completado en {language}!**\n\n"
            f"✅ Grupos creados: {grupos_creados}\n"
            f"❌ Grupos fallidos: {grupos_fallidos}\n"
            f"👤 Sesión utilizada: {user_name}"
        )
        
        # Enviar resumen en chunks
        chunk_size = 10
        for i in range(0, len(resultados), chunk_size):
            chunk = resultados[i:i + chunk_size]
            await message.reply("\n".join(chunk))
            await asyncio.sleep(2)

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

async def restart_user_client(user_id):
    """Reiniciar el cliente de usuario para un usuario específico"""
    user_data = user_sessions.get(user_id, {})
    if user_data and "client" in user_data and user_data["client"].is_connected:
        await user_data["client"].stop()
        user_sessions[user_id]["active"] = False
    
    if await initialize_user_client(user_id):
        print(f"✅ Cliente de usuario {user_id} reiniciado")
        return True
    else:
        print(f"❌ Error reiniciando cliente {user_id}")
        return False

# Función para registrar los handlers después de inicializar el bot
def register_handlers():
    """Registrar todos los handlers después de inicializar el bot"""
    
    @bot_client.on_message(filters.command("set") & filters.private)
    async def set_session_command(client: Client, message: Message):
        user_id = message.from_user.id
        
        if len(message.command) < 2:
            await message.reply("❌ Uso: /set <session_string>")
            return
        
        session_string = message.command[1]
        user_sessions[user_id] = {
            "session_string": session_string,
            "client": None,
            "active": False,
            "user_name": "Sin configurar"
        }
        
        if save_sessions():
            await message.reply("✅ Sesión guardada. Reconectando...")
            if await initialize_user_client(user_id):
                user_name = user_sessions[user_id].get("user_name", "Usuario")
                await message.reply(f"✅ Sesión configurada correctamente\n👤 Usuario: {user_name}")
            else:
                await message.reply("❌ Error iniciando sesión. Verifica el session_string.")
        else:
            await message.reply("❌ Error guardando sesión")

    @bot_client.on_message(filters.command("login") & filters.private)
    async def login_command(client: Client, message: Message):
        user_id = message.from_user.id
        
        # Limpiar estado anterior si existe
        if user_id in login_states:
            if "client" in login_states[user_id] and login_states[user_id]["client"]:
                try:
                    await login_states[user_id]["client"].stop()
                except:
                    pass
            del login_states[user_id]
        
        # Crear nuevo cliente para el proceso de login
        login_client = Client(
            f"login_session_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            in_memory=True
        )
        
        login_states[user_id] = {
            "step": "phone",
            "client": login_client
        }
        
        await message.reply(
            "🔑 **Iniciar sesión en Telegram**\n\n"
            "Por favor, envía tu número de teléfono en formato internacional.\n"
            "Ejemplo: +1234567890"
        )

    @bot_client.on_message(filters.command("creargrupos") & filters.private)
    async def crear_grupos_command(client: Client, message: Message):
        user_id = message.from_user.id
        
        if user_id not in user_sessions or not user_sessions[user_id].get("session_string"):
            await message.reply("❌ Configura una sesión con /set <session_string> o usa /login")
            return
        
        # Verificar si el cliente está activo
        if not user_sessions[user_id].get("active", False):
            if not await initialize_user_client(user_id):
                await message.reply("❌ Error iniciando sesión. Usa /set nuevamente.")
                return
        
        try:
            # Mostrar opciones de idioma
            user_name = user_sessions[user_id].get("user_name", "Usuario")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🇪🇸 Español", callback_data=f"lang_es_{user_id}")],
                [InlineKeyboardButton("🇺🇸 Inglés", callback_data=f"lang_en_{user_id}")],
                [InlineKeyboardButton("🇷🇺 Ruso", callback_data=f"lang_ru_{user_id}")],
                [InlineKeyboardButton("🇸🇦 Árabe", callback_data=f"lang_ar_{user_id}")]
            ])
            
            await message.reply(
                f"🌍 **Selecciona el idioma para los mensajes aleatorios:**\n"
                f"👤 Sesión actual: {user_name}",
                reply_markup=keyboard
            )
            
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")

    @bot_client.on_callback_query()
    async def handle_callbacks(client: Client, callback_query):
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Extraer el user_id del callback_data si está presente
        if any(data.startswith(prefix) for prefix in ["confirm_yes_", "confirm_no_", "lang_", "test_"]):
            target_user_id = int(data.split("_")[2])
            if user_id != target_user_id:
                await callback_query.answer("❌ Esta confirmación no es para ti")
                return
        
        if data.startswith("confirm_yes_"):
            language = language_selection.get(user_id, {}).get("language", "español")
            user_name = user_sessions.get(user_id, {}).get("user_name", "Usuario")
            confirmaciones_activas[user_id] = False
            await callback_query.message.edit("✅ Confirmado. Iniciando...")
            await crear_grupos(callback_query.message, user_id, language)
        elif data.startswith("confirm_no_"):
            confirmaciones_activas[user_id] = False
            await callback_query.message.edit("❌ Cancelado.")
        elif data.startswith("lang_"):
            lang_code = data.split("_")[1]
            lang_map = {
                "es": "español",
                "en": "ingles",
                "ru": "ruso",
                "ar": "árabe"
            }
            
            selected_language = lang_map.get(lang_code, "español")
            language_selection[user_id] = {"language": selected_language}
            user_name = user_sessions.get(user_id, {}).get("user_name", "Usuario")
            
            # Ahora pedir confirmación
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ SI", callback_data=f"confirm_yes_{user_id}")],
                [InlineKeyboardButton("❌ NO", callback_data=f"confirm_no_{user_id}")]
            ])
            
            await callback_query.message.edit(
                f"⚠️ **ADVERTENCIA** ⚠️\n\n"
                f"Vas a crear 50 grupos con mensajes aleatorios en {selected_language}.\n"
                f"👤 Sesión que se usará: {user_name}\n\n"
                "Esto puede:\n"
                "• Ser detectado como spam\n"
                "• Causar limitaciones temporales\n\n"
                "¿Continuar?",
                reply_markup=keyboard
            )
            
            confirmaciones_activas[user_id] = True
        
        elif data.startswith("test_"):
            lang_code = data.split("_")[1]
            lang_map = {
                "es": "español",
                "en": "ingles",
                "ru": "ruso",
                "ar": "árabe"
            }
            
            selected_language = lang_map.get(lang_code, "español")
            
            # Ejecutar prueba con 2 grupos
            # Ejecutar prueba con 2 grupos
            user_data = user_sessions.get(user_id, {})
            if not user_data or "client" not in user_data:
                await callback_query.message.edit("❌ Error: Sesión no configurada")
                return
            
            client = user_data["client"]
            user_name = user_data.get("user_name", "Usuario")
            await callback_query.message.edit(f"🧪 Probando con 2 grupos en {selected_language} (Sesión: {user_name})...")
            
            grupos_test_creados = 0
            for i in range(1, 3):
                try:
                    group_name = generate_random_name()
                    group = await client.create_supergroup(
                        title=group_name,
                        description=f"Grupo prueba #{i} - Sesión: {user_name}"
                    )
                    
                    # Enviar mensajes aleatorios al grupo de prueba (sin username)
                    await enviar_mensajes_aleatorios(client, group.id, selected_language)
                    
                    grupos_test_creados += 1
                    await callback_query.message.reply(f"✅ Grupo {i}: {group_name} (Sesión: {user_name})")
                    await asyncio.sleep(3)
                except Exception as e:
                    error_msg = "Límite de flood" if "FLOOD" in str(e).upper() else str(e)
                    await callback_query.message.reply(f"❌ Error {i}: {error_msg} (Sesión: {user_name})")
                    break
            
            await callback_query.message.reply(f"🧪 Prueba completada: {grupos_test_creados}/2 grupos (Sesión: {user_name})")
        
        await callback_query.answer()

    @bot_client.on_message(filters.command("start") & filters.private)
    async def start_command(client: Client, message: Message):
        user_id = message.from_user.id
        user_has_session = user_id in user_sessions and user_sessions[user_id].get("session_string")
        
        if not user_has_session:
            await message.reply(
                "🤖 **Bot Creador de Grupos**\n\n"
                "⚠️ Configura una sesión primero:\n"
                "/login - Iniciar sesión interactivamente\n"
                "/set <session_string> - Usar session string existente\n\n"
                "Para obtener session_string manualmente:\n"
                "1. Visita https://replit.com/@ayrahikari/pyrogram-session-string\n"
                "2. Genera tu session_string\n"
                "3. Usa /set <codigo>"
            )
        else:
            user_name = user_sessions[user_id].get("user_name", "Usuario")
            await message.reply(
                f"🤖 **Bot Creador de Grupos**\n\n"
                f"✅ Sesión configurada - 👤 {user_name}\n\n"
                "Comandos:\n"
                "/creargrupos - Crear 50 grupos con mensajes aleatorios\n"
                "/test - Probar con 2 grupos\n"
                "/estado - Ver estado\n"
                "/setsession - Cambiar sesión\n"
                "/login - Iniciar nueva sesión"
            )

    @bot_client.on_message(filters.command("test") & filters.private)
    async def test_command(client: Client, message: Message):
        user_id = message.from_user.id
        
        if user_id not in user_sessions or not user_sessions[user_id].get("session_string"):
            await message.reply("❌ Configura una sesión con /set o /login")
            return
        
        # Verificar si el cliente está activo
        if not user_sessions[user_id].get("active", False):
            if not await initialize_user_client(user_id):
                await message.reply("❌ Error iniciando sesión. Usa /set nuevamente.")
                return
        
        try:
            user_name = user_sessions[user_id].get("user_name", "Usuario")
            # Mostrar opciones de idioma para test
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🇪🇸 Español", callback_data=f"test_es_{user_id}")],
                [InlineKeyboardButton("🇺🇸 Inglés", callback_data=f"test_en_{user_id}")],
                [InlineKeyboardButton("🇷🇺 Ruso", callback_data=f"test_ru_{user_id}")],
                [InlineKeyboardButton("🇸🇦 Árabe", callback_data=f"test_ar_{user_id}")]
            ])
            
            await message.reply(
                f"🌍 **Selecciona el idioma para la prueba:**\n"
                f"👤 Sesión actual: {user_name}",
                reply_markup=keyboard
            )
            
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")

    @bot_client.on_message(filters.command("estado") & filters.private)
    async def estado_command(client: Client, message: Message):
        user_id = message.from_user.id
        user_has_session = user_id in user_sessions and user_sessions[user_id].get("session_string")
        
        status = "✅ Configurada\n" if user_has_session else "❌ No configurada\n"
        user_conn = "✅ Conectado\n" if user_has_session and user_sessions[user_id].get("active", False) else "❌ Desconectado\n"
        bot_conn = "✅ Conectado\n" if bot_client and bot_client.is_connected else "❌ Desconectado\n"
        
        # Obtener información del nombre de usuario si existe la sesión
        user_name_info = ""
        if user_has_session:
            user_name = user_sessions[user_id].get("user_name", "Sin nombre")
            user_name_info = f"👤 Nombre de sesión: {user_name}\n"
        
        await message.reply(
            f"🤖 **Estado para usuario {user_id}:**\n\n"
            f"**Sesión:** {status}"
            f"**Usuario:** {user_conn}"
            f"**Bot:** {bot_conn}"
            f"{user_name_info}"
        )

    @bot_client.on_message(filters.command("setsession") & filters.private)
    async def change_session_command(client: Client, message: Message):
        await message.reply(
            "🔄 Para cambiar sesión:\n\n"
            "1. Usa /login para iniciar sesión interactivamente\n"
            "O\n"
            "2. Visita https://replit.com/@ayrahikari/pyrogram-session-string\n"
            "3. Genera nueva session_string\n"
            "4. Usa /set <nuevo_codigo>"
        )

    @bot_client.on_message(filters.private & ~filters.command(["start", "set", "login", "creargrupos", "test", "estado", "setsession"]))
    async def handle_messages(client: Client, message: Message):
        user_id = message.from_user.id
        
        # Si el usuario está en proceso de login
        if user_id in login_states:
            state = login_states[user_id]
            
            try:
                if state["step"] == "phone":
                    # Paso 1: Solicitar número de teléfono
                    phone_number = message.text.strip()
                    
                    # Validar formato básico de número
                    if not phone_number.startswith('+'):
                        await message.reply("❌ Formato incorrecto. Debe empezar con + (ej: +1234567890). Intenta de nuevo:")
                        return
                    
                    # Iniciar cliente
                    login_client = state["client"]
                    await login_client.connect()
                    
                    # Solicitar código
                    sent_code = await login_client.send_code(phone_number)
                    state["step"] = "code"
                    state["phone_number"] = phone_number
                    state["phone_code_hash"] = sent_code.phone_code_hash
                    
                    await message.reply(
                        "📲 **Código de verificación**\n\n"
                        "Se ha enviado un código a tu cuenta de Telegram.\n"
                        "Por favor, ingresa el código recibido (formato: 1 2 3 4 5):"
                    )
                
                elif state["step"] == "code":
                    # Paso 2: Solicitar código de verificación
                    code = message.text.strip().replace(' ', '')  # Quitar espacios
                    
                    if not code.isdigit() or len(code) != 5:
                        await message.reply("❌ Código inválido. Debe ser un número de 5 dígitos. Intenta de nuevo:")
                        return
                    
                    try:
                        # Intentar iniciar sesión con el código
                        await state["client"].sign_in(
                            phone_number=state["phone_number"],
                            phone_code_hash=state["phone_code_hash"],
                            phone_code=code
                        )
                        
                        # Éxito - obtener session string
                        session_string = await state["client"].export_session_string()
                        
                        # Obtener información del usuario (nombre)
                        me = await state["client"].get_me()
                        user_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
                        if not user_name:
                            user_name = f"Usuario {user_id}"
                        
                        # Guardar sesión
                        user_sessions[user_id] = {
                            "session_string": session_string,
                            "client": None,
                            "active": False,
                            "user_name": user_name
                        }
                        
                        save_sessions()
                        
                        # Inicializar cliente
                        await initialize_user_client(user_id)
                        
                        await message.reply(
                            f"✅ **Sesión iniciada correctamente!**\n\n"
                            f"👤 Usuario: {user_name}\n\n"
                            f"Tu session_string es:\n`{session_string}`\n\n"
                            f"Guarda este código para usarlo luego con /set"
                        )
                        
                        # Limpiar estado de login
                        await state["client"].disconnect()
                        del login_states[user_id]
                        
                    except SessionPasswordNeeded:
                        state["step"] = "password"
                        await message.reply(
                            "🔐 **Verificación en dos pasos**\n\n"
                            "Tu cuenta tiene habilitada la verificación en dos pasos.\n"
                            "Por favor, ingresa tu contraseña:"
                        )
                    
                    except PhoneCodeInvalid:
                        await message.reply("❌ Código inválido. Intenta de nuevo:")
                
                elif state["step"] == "password":
                    # Paso 3: Solicitar contraseña 2FA
                    password = message.text.strip()
                    
                    try:
                        await state["client"].check_password(password)
                        
                        # Éxito - obtener session string
                        session_string = await state["client"].export_session_string()
                        
                        # Obtener información del usuario (nombre)
                        me = await state["client"].get_me()
                        user_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
                        if not user_name:
                            user_name = f"Usuario {user_id}"
                        
                        # Guardar sesión
                        user_sessions[user_id] = {
                            "session_string": session_string,
                            "client": None,
                            "active": False,
                            "user_name": user_name
                        }
                        
                        save_sessions()
                        
                        # Inicializar cliente
                        await initialize_user_client(user_id)
                        
                        await message.reply(
                            f"✅ **Sesión iniciada correctamente!**\n\n"
                            f"👤 Usuario: {user_name}\n\n"
                            f"Tu session_string es:\n`{session_string}`\n\n"
                            f"Guarda este código para usarlo luego con /set"
                        )
                        
                        # Limpiar estado de login
                        await state["client"].disconnect()
                        del login_states[user_id]
                        
                    except Exception as e:
                        await message.reply(f"❌ Error: {str(e)}\nIntenta de nuevo:")
            
            except PhoneNumberInvalid:
                await message.reply("❌ Número de teléfono inválido. Intenta de nuevo:")
                state["step"] = "phone"
            except Exception as e:
                await message.reply(f"❌ Error: {str(e)}\nEl proceso de login se ha cancelado.")
                if "client" in state and state["client"]:
                    try:
                        await state["client"].disconnect()
                    except:
                        pass
                del login_states[user_id]
        
        else:
            # Mensaje no reconocido
            await message.reply(
                "🤖 **Comandos disponibles:**\n\n"
                "/start - Iniciar bot\n"
                "/login - Iniciar sesión\n"
                "/set - Configurar sesión\n"
                "/creargrupos - Crear grupos con mensajes aleatorios\n"
                "/test - Probar con 2 grupos\n"
                "/estado - Ver estado\n"
                "/setsession - Cambiar sesión"
            )

async def main():
    """Función principal"""
    print("🤖 Iniciando Bot Creador de Grupos...")
    
    # Cargar sesiones existentes
    load_sessions()
    
    # Inicializar bot
    if not initialize_bot_client():
        print("❌ Error inicializando bot")
        return
    
    # Registrar handlers
    register_handlers()
    
    # Iniciar bot
    try:
        await bot_client.start()
        print("✅ Bot iniciado correctamente")
        
        # Inicializar clientes de usuario existentes
        for user_id in list(user_sessions.keys()):
            if user_sessions[user_id].get("session_string"):
                await initialize_user_client(user_id)
        
        # Mantener el bot corriendo
        await idle()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Guardar sesiones al cerrar
        save_sessions()
        
        # Cerrar conexiones
        if bot_client and bot_client.is_connected:
            await bot_client.stop()
        
        for user_id, data in user_sessions.items():
            if "client" in data and data["client"] and data["client"].is_connected:
                await data["client"].stop()
        
        print("👋 Bot detenido")

if __name__ == "__main__":
    asyncio.run(main())