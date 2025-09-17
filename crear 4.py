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
user_sessions = defaultdict(dict)  # {user_id: {"session_string": "", "client": None, "active": False, "username": ""}}
confirmaciones_activas = {}  # {user_id: True/False}
login_states = {}  # {user_id: {"step": "phone", "phone_code_hash": "", "client": None}}
user_languages = {}  # {user_id: "es"/"ru"/"ar"}

# Archivo para guardar las sesiones de usuarios
SESSIONS_FILE = "user_sessions.json"

# Mensajes en diferentes idiomas
MESSAGES = {
    "es": {
        "creation_date": "📅 **Fecha de creación:** {fecha_creacion}",
        "creation_time": "⏰ **Hora de creación:** {hora_creacion}",
        "created_by": "👤 **Creado por:** @{username}",
        "group_name": "🏷️ **Nombre del grupo:** {group_name}",
        "welcome": "👋 ¡Bienvenidos al grupo! Este grupo fue creado automáticamente. ¡Disfruten de la estadía!",
        "info": "ℹ️ **Información:**\n\n• Grupo creado con un bot de automatización\n• Pueden personalizar este grupo como deseen\n• ¡Diviértanse!",
        "rules": "📋 **Reglas del grupo:**\n\n• Respetar a todos los miembros\n• No spam ni contenido inapropiado\n• Mantener conversaciones civilizadas",
        "invite": "👥 **¡Invita a tus amigos!**\n\nComparte este grupo con personas que puedan estar interesadas en nuestra comunidad. ¡Entre más, mejor!",
        "topics": "💬 **Temas de conversación:**\n\n• Tecnología y programación\n• Noticias y actualidades\n• Música y entretenimiento\n• Deportes y hobbies",
        "final": "🎉 **¡Que comience la conversación!**\n\nNo dudes en iniciar algún tema interesante. ¡Todos están invitados a participar!"
    },
    "ru": {
        "creation_date": "📅 **Дата создания:** {fecha_creacion}",
        "creation_time": "⏰ **Время создания:** {hora_creacion}",
        "created_by": "👤 **Создано:** @{username}",
        "group_name": "🏷️ **Название группы:** {group_name}",
        "welcome": "👋 Добро пожаловать в группу! Эта группа была создана автоматически. Приятного пребывания!",
        "info": "ℹ️ **Информация:**\n\n• Группа создана с помощью бота автоматизации\n• Вы можете настроить эту группу по своему желанию\n• Развлекайтесь!",
        "rules": "📋 **Правила группы:**\n\n• Уважайте всех участников\n• Не спамить и не размещать неподходящий контент\n• Поддерживайте цивилизованные разговоры",
        "invite": "👥 **Пригласите своих друзей!**\n\nПоделитесь этой группой с людьми, которые могут быть заинтересованы в нашем сообществе. Чем больше, тем лучше!",
        "topics": "💬 **Темы для разговора:**\n\n• Технологии и программирование\n• Новости и текущие события\n• Музыка и развлечения\n• Спорт и хобби",
        "final": "🎉 **Пусть начнется разговор!**\n\nНе стесняйтесь начинать интересные темы. Все приглашены к участию!"
    },
    "ar": {
        "creation_date": "📅 **تاريخ الإنشاء:** {fecha_creacion}",
        "creation_time": "⏰ **وقت الإنشاء:** {hora_creacion}",
        "created_by": "👤 **تم الإنشاء بواسطة:** @{username}",
        "group_name": "🏷️ **اسم المجموعة:** {group_name}",
        "welcome": "👋 مرحبًا بكم في المجموعة! تم إنشاء هذه المجموعة تلقائيًا. استمتع بإقامتك!",
        "info": "ℹ️ **معلومات:**\n\n• تم إنشاء المجموعة باستخدام بوت الأتمتة\n• يمكنك تخصيص هذه المجموعة كما تريد\n• استمتع!",
        "rules": "📋 **قواعد المجموعة:**\n\n• احترم جميع الأعضاء\n• لا للبريد المزعج أو المحتوى غير المناسب\n• الحفاظ على المحادثات مهذبة",
        "invite": "👥 **ادعُ أصدقاءك!**\n\nشارك هذه المجموعة مع الأشخاص الذين قد يكونون مهتمين بمجتمعنا. كلما زاد العدد كان ذلك أفضل!",
        "topics": "💬 **مواضيع المحادثة:**\n\n• التكنولوجيا والبرمجة\n• الأخبار والأحداث الجارية\n• الموسيقى والترفيه\n• الرياضة والهوايات",
        "final": "🎉 **لتبدأ المحادثة!**\n\nلا تتردد في بدء موضوع مثير للاهتمام. الجميع مدعو للمشاركة!"
    }
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
                "username": session_data.get("username", "")
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
        
        # Guardar el nombre de usuario
        if not user_sessions[user_id].get("username"):
            user_sessions[user_id]["username"] = user_client.me.username if user_client.me.username else f"user{user_id}"
            save_sessions()
            
        return True
    except Exception as e:
        print(f"Error inicializando cliente de usuario {user_id}: {e}")
        user_sessions[user_id]["active"] = False
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

async def enviar_mensajes_al_grupo(client, group_id, group_name, lang="es"):
    """Envía mensajes al grupo recién creado en el idioma seleccionado"""
    try:
        # Obtener fecha actual
        now = datetime.datetime.now()
        fecha_creacion = now.strftime("%d/%m/%Y")
        hora_creacion = now.strftime("%H:%M:%S")
        
        # Obtener mensajes en el idioma seleccionado
        msgs = MESSAGES.get(lang, MESSAGES["es"])
        username = client.me.username if client.me.username else "Usuario"
        
        # Mensaje 1: Información de creación
        await client.send_message(
            group_id,
            f"{msgs['creation_date'].format(fecha_creacion=fecha_creacion)}\n"
            f"{msgs['creation_time'].format(hora_creacion=hora_creacion)}\n"
            f"{msgs['created_by'].format(username=username)}"
        )
        
        await asyncio.sleep(2)
        
        # Mensaje 2: Nombre del grupo
        await client.send_message(
            group_id,
            msgs['group_name'].format(group_name=group_name)
        )
        
        await asyncio.sleep(2)
        
        # Mensaje 3: Mensaje de bienvenida
        await client.send_message(
            group_id,
            msgs['welcome']
        )
        
        await asyncio.sleep(2)
        
        # Mensaje 4: Información adicional
        await client.send_message(
            group_id,
            msgs['info']
        )
        
        await asyncio.sleep(2)
        
        # MENSAJES ADICIONALES (4 mensajes más)
        
        # Mensaje 5: Reglas básicas
        await client.send_message(
            group_id,
            msgs['rules']
        )
        
        await asyncio.sleep(2)
        
        # Mensaje 6: Invitación a invitar amigos
        await client.send_message(
            group_id,
            msgs['invite']
        )
        
        await asyncio.sleep(2)
        
        # Mensaje 7: Sugerencia de temas
        await client.send_message(
            group_id,
            msgs['topics']
        )
        
        await asyncio.sleep(2)
        
        # Mensaje 8: Mensaje final de cierre
        await client.send_message(
            group_id,
            msgs['final']
        )
        
        return True
    except Exception as e:
        print(f"Error enviando mensajes al grupo {group_name}: {e}")
        return False

async def crear_grupos(message: Message, user_id):
    """Función que crea los grupos para un usuario específico"""
    try:
        user_data = user_sessions.get(user_id, {})
        if not user_data or "client" not in user_data or not user_data["client"].is_connected:
            await message.reply("❌ Cliente de usuario no conectado. Usa /set primero.")
            return
            
        client = user_data["client"]
        username = user_data.get("username", "Usuario")
        lang = user_languages.get(user_id, "es")
        
        progress_msg = await message.reply(f"🔄 Creando 50 grupos en la cuenta @{username}...\n\n0/50 completados")
        
        grupos_creados = 0
        grupos_fallidos = 0
        resultados = []

        for i in range(1, 51):
            try:
                # Crear supergrupo
                group_name = generate_random_name()
                group = await client.create_supergroup(
                    title=group_name,
                    description=f"Grupo automático #{i}"
                )

                # Obtener ID del grupo
                group_id = group.id
                
                # Enviar mensajes al grupo
                mensajes_enviados = await enviar_mensajes_al_grupo(client, group_id, group_name, lang)
                
                grupos_creados += 1
                resultado = f"✅ Grupo {i}: {group_name}"
                if not mensajes_enviados:
                    resultado += " (error enviando mensajes)"
                resultados.append(resultado)
                
                # Actualizar progreso cada 5 grupos
                if i % 5 == 0:
                    await progress_msg.edit_text(
                        f"🔄 Creando grupos en @{username}...\n\n{i}/50 completados\n"
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
            f"🎉 **Proceso completado en @{username}!**\n\n"
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
            "username": ""
        }
        
        if save_sessions():
            await message.reply("✅ Sesión guardada. Reconectando...")
            if await initialize_user_client(user_id):
                username = user_sessions[user_id].get("username", "Usuario")
                await message.reply(f"✅ Sesión configurada correctamente para @{username}")
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
            # Primero preguntar por el idioma
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🇪🇸 Español", callback_data=f"lang_es_{user_id}")],
                [InlineKeyboardButton("🇷🇺 Ruso", callback_data=f"lang_ru_{user_id}")],
                [InlineKeyboardButton("🇸🇦 Árabe", callback_data=f"lang_ar_{user_id}")]
            ])
            
            await message.reply(
                "🌍 **Selecciona el idioma para los mensajes de los grupos:**",
                reply_markup=keyboard
            )
            
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")

    @bot_client.on_callback_query()
    async def handle_callbacks(client: Client, callback_query):
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Extraer el user_id del callback_data si está presente
        if any(data.startswith(prefix) for prefix in ["confirm_yes_", "confirm_no_", "lang_"]):
            target_user_id = int(data.split("_")[2])
            if user_id != target_user_id:
                await callback_query.answer("❌ Esta confirmación no es para ti")
                return
        
        if data.startswith("lang_"):
            lang = data.split("_")[1]
            user_languages[user_id] = lang
            
            langs = {"es": "Español", "ru": "Ruso", "ar": "Árabe"}
            await callback_query.message.edit(f"🌍 Idioma seleccionado: {langs[lang]}")
            
            # Ahora mostrar la confirmación de creación de grupos
            username = user_sessions[user_id].get("username", "Usuario")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ SI", callback_data=f"confirm_yes_{user_id}")],
                [InlineKeyboardButton("❌ NO", callback_data=f"confirm_no_{user_id}")]
            ])
            
            await callback_query.message.reply(
                f"⚠️ **ADVERTENCIA** ⚠️\n\n"
                f"Vas a crear 50 grupos en la cuenta @{username} con mensajes en {langs[lang]}. Esto puede:\n"
                "• Ser detectado como spam\n"
                "• Causar limitaciones temporales\n\n"
                "¿Continuar?",
                reply_markup=keyboard
            )
            
            confirmaciones_activas[user_id] = True
            
        elif data.startswith("confirm_yes_"):
            confirmaciones_activas[user_id] = False
            await callback_query.message.edit("✅ Confirmado. Iniciando...")
            await crear_grupos(callback_query.message, user_id)
        elif data.startswith("confirm_no_"):
            confirmaciones_activas[user_id] = False
            await callback_query.message.edit("❌ Cancelado.")
        
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
            username = user_sessions[user_id].get("username", "Usuario")
            await message.reply(
                f"🤖 **Bot Creador de Grupos**\n\n"
                f"✅ Sesión configurada para @{username}\n\n"
                "Comandos:\n"
                "/creargrupos - Crear 50 grupos\n"
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
            user_client = user_sessions[user_id]["client"]
            username = user_sessions[user_id].get("username", "Usuario")
            lang = user_languages.get(user_id, "es")
            await message.reply(f"🧪 Probando con 2 grupos en @{username}...")
            grupos_test_creados = 0
            
            for i in range(1, 3):
                try:
                    group_name = generate_random_name()
                    group = await user_client.create_supergroup(
                        title=group_name,
                        description=f"Grupo prueba #{i}"
                    )
                    
                    # Enviar mensajes al grupo de prueba
                    await enviar_mensajes_al_grupo(user_client, group.id, group_name, lang)
                    
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
        user_id = message.from_user.id
        user_has_session = user_id in user_sessions and user_sessions[user_id].get("session_string")
        
        status = "✅ Configurada\n" if user_has_session else "❌ No configurada\n"
        username = user_sessions[user_id].get("username", "No configurado") if user_has_session else "No configurado"
        user_conn = "✅ Conectado\n" if user_has_session and user_sessions[user_id].get("active", False) else "❌ Desconectado\n"
        bot_conn = "✅ Conectado\n" if bot_client and bot_client.is_connected else "❌ Desconectado\n"
        lang = user_languages.get(user_id, "es")
        lang_name = {"es": "Español", "ru": "Ruso", "ar": "Árabe"}.get(lang, "Español")
        
        await message.reply(
            f"🤖 **Estado para usuario {user_id}:**\n\n"
            f"**Sesión:** {status}"
            f"**Usuario:** @{username}\n"
            f"**Conexión usuario:** {user_conn}"
            f"**Conexión bot:** {bot_conn}"
            f"**Idioma:** {lang_name}"
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
                        
                        # Guardar sesión
                        user_sessions[user_id] = {
                            "session_string": session_string,
                            "client": None,
                            "active": False,
                            "username": state["client"].me.username if state["client"].me.username else f"user{user_id}"
                        }
                        
                        save_sessions()
                        
                        # Inicializar cliente
                        await initialize_user_client(user_id)
                        
                        username = user_sessions[user_id].get("username", "Usuario")
                        await message.reply(
                            f"✅ **Sesión iniciada correctamente para @{username}!**\n\n"
                            f"Tu session_string es:\n`{session_string}`\n\n"
                            f"Guarda este código para usarlo luego con /set"
                        )
                        
                        # Limpiar estado de login
                        await state["client"].disconnect()
                        del login_states[user_id]
                        
                    except SessionPasswordNeeded:
                        # Se requiere contraseña 2FA
                        state["step"] = "password"
                        await message.reply(
                            "🔒 **Verificación en dos pasos**\n\n"
                            "Tu cuenta tiene habilitada la verificación en dos pasos.\n"
                            "Por favor, ingresa tu contraseña:"
                        )
                    
                    except PhoneCodeInvalid:
                        await message.reply("❌ Código inválido. Intenta de nuevo:")
                    
                    except Exception as e:
                        await message.reply(f"❌ Error: {str(e)}")
                        # Limpiar estado en caso de error
                        await state["client"].disconnect()
                        del login_states[user_id]
                
                elif state["step"] == "password":
                    # Paso 3: Solicitar contraseña 2FA
                    password = message.text.strip()
                    
                    try:
                        # Verificar contraseña
                        await state["client"].check_password(password)
                        
                        # Éxito - obtener session string
                        session_string = await state["client"].export_session_string()
                        
                        # Guardar sesión
                        user_sessions[user_id] = {
                            "session_string": session_string,
                            "client": None,
                            "active": False,
                            "username": state["client"].me.username if state["client"].me.username else f"user{user_id}"
                        }
                        
                        save_sessions()
                        
                        # Inicializar cliente
                        await initialize_user_client(user_id)
                        
                        username = user_sessions[user_id].get("username", "Usuario")
                        await message.reply(
                            f"✅ **Sesión iniciada correctamente para @{username}!**\n\n"
                            f"Tu session_string es:\n`{session_string}`\n\n"
                            f"Guarda este código para usarlo luego con /set"
                        )
                        
                        # Limpiar estado de login
                        await state["client"].disconnect()
                        del login_states[user_id]
                        
                    except Exception as e:
                        await message.reply(f"❌ Contraseña incorrecta. Intenta de nuevo: {str(e)}")
            
            except Exception as e:
                await message.reply(f"❌ Error en el proceso de login: {str(e)}")
                # Limpiar estado en caso de error
                if user_id in login_states and "client" in login_states[user_id]:
                    try:
                        await login_states[user_id]["client"].disconnect()
                    except:
                        pass
                if user_id in login_states:
                    del login_states[user_id]
                    
                    
             # Función principal
async def main():
    # Verificar token primero
    if BOT_TOKEN == "TU_BOT_TOKEN_AQUI":
        print("❌ ERROR: Debes reemplazar BOT_TOKEN con tu token real de @BotFather")
        return
    
    # Cargar sesiones existentes
    load_sessions()
    
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
        
        # Inicializar clientes de usuario para quienes tengan sesión
        for user_id in list(user_sessions.keys()):
            await initialize_user_client(user_id)
        
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
        for user_id, user_data in user_sessions.items():
            if "client" in user_data and user_data["client"] and user_data["client"].is_connected:
                await user_data["client"].stop()
        
        # Cerrar clientes de login activos
        for user_id, state in login_states.items():
            if "client" in state and state["client"]:
                try:
                    await state["client"].disconnect()
                except:
                    pass
        
        if bot_client and bot_client.is_connected:
            await bot_client.stop()

if __name__ == "__main__":
    # Crear archivo de sesiones si no existe
    if not os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'w') as f:
                json.dump({}, f)
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
