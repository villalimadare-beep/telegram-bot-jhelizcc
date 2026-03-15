import sqlite3
from datetime import datetime
from pathlib import Path
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# =========================
# CONFIGURACION
# =========================
TOKEN = "8270045138:AAEc-wpdLJKk5RGTQck7tHrw5lLGMaiKIkM"
ADMIN_IDS = {8228056019}  # Reemplaza por tu user_id real
DB_NAME = "database.db"
QR_PATH = Path("qr/yape.png")
MARCA = "@jhelizccventas"

MENU, WAITING_PLATFORM, WAITING_PROOF, WAITING_SUPPORT, WAITING_SUPPORT_RESPONSE = range(5)

# =========================
# BASE DE DATOS
# =========================
def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clave TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nombre TEXT,
            username TEXT,
            plataforma TEXT NOT NULL,
            precio REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            comprobante TEXT,
            comprobante_file_id TEXT,
            correo_asignado TEXT,
            password_asignado TEXT,
            perfil_asignado TEXT,
            fecha_vencimiento TEXT,
            fecha_creacion TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            cliente_user_id INTEGER,
            cliente_nombre TEXT,
            plataforma TEXT,
            correo TEXT,
            perfil TEXT,
            fecha_vencimiento TEXT,
            estado TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS renovaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nombre TEXT,
            plataforma TEXT,
            perfil TEXT,
            respuesta TEXT,
            fecha TEXT NOT NULL
        )
    """)

    productos_base = [
        ("netflix", "Netflix", 20),
        ("disney", "Disney+", 25),
        ("max", "Max", 20),
        ("prime", "Prime Video", 15),
        ("crunchy", "Crunchyroll", 12),
    ]

    for clave, nombre, precio in productos_base:
        cur.execute(
            """
            INSERT OR IGNORE INTO productos (clave, nombre, precio)
            VALUES (?, ?, ?)
            """,
            (clave, nombre, precio),
        )

    conn.commit()
    conn.close()


# =========================
# UTILIDADES
# =========================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🛍️ Ver catálogo"), KeyboardButton("💳 Comprar ahora")],
            [KeyboardButton("📦 Mi pedido"), KeyboardButton("🛠️ Soporte")],
            [KeyboardButton("📘 Cómo comprar"), KeyboardButton("ℹ️ Información")],
            [KeyboardButton("🔄 Renovar")],
        ],
        resize_keyboard=True,
    )


def platform_keyboard():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT clave, nombre, precio FROM productos ORDER BY nombre ASC")
    rows = cur.fetchall()
    conn.close()

    botones = []
    for row in rows:
        botones.append([
            InlineKeyboardButton(
                f"{row['nombre']} — S/{row['precio']}",
                callback_data=f"buy:{row['clave']}"
            )
        ])

    botones.append([InlineKeyboardButton("⬅ Volver", callback_data="back_menu")])
    return InlineKeyboardMarkup(botones)


# =========================
# CLIENTE
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ *Bienvenido(a) a JHELIZCC VENTAS* ✨\n\n"
        "🎬 Tu tienda digital de confianza para accesos de streaming.\n\n"
        "Aquí podrás:\n"
        "🛍️ Ver plataformas disponibles\n"
        "💳 Comprar tu acceso\n"
        "📦 Revisar tu pedido\n"
        "🛠️ Solicitar soporte\n"
        "🔔 Recibir aviso de vencimiento\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "💎 *¿Por qué elegirnos?*\n\n"
        "⚡ Atención rápida\n"
        "🔐 Accesos seguros\n"
        "📲 Soporte directo\n"
        "💰 Precios accesibles\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"💙 *Marca oficial*\n{MARCA}\n\n"
        "👇 Selecciona una opción del menú para comenzar",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )
    return MENU


async def catalogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT nombre, precio FROM productos ORDER BY nombre ASC")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No hay productos disponibles.")
        return

    texto = "🛍️ *CATÁLOGO DISPONIBLE*\n\n"
    for row in rows:
        texto += f"📺 *{row['nombre']}* — *S/{row['precio']}*\n"

    texto += (
        "\n━━━━━━━━━━━━━━━━━━\n\n"
        "✨ Accesos digitales con atención personalizada.\n"
        "💳 Para comprar, toca *Comprar ahora*.\n\n"
        f"💙 {MARCA}"
    )

    await update.message.reply_text(texto, parse_mode="Markdown")


async def comprar_ahora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💳 *ELIGE TU PLATAFORMA*\n\n"
        "Selecciona una opción para continuar con tu compra 👇",
        reply_markup=platform_keyboard(),
        parse_mode="Markdown",
    )
    return WAITING_PLATFORM


async def como_comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📘 *CÓMO COMPRAR EN JHELIZCC VENTAS*\n\n"
        "Sigue estos pasos 👇\n\n"
        "1️⃣ Toca *Ver catálogo*\n"
        "2️⃣ Elige la plataforma que deseas\n"
        "3️⃣ Escanea el QR y realiza tu pago\n"
        "4️⃣ Envía tu comprobante en este chat\n"
        "5️⃣ Un administrador validará tu compra\n"
        "6️⃣ Recibirás tus datos de acceso\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Recibirás:\n"
        "📧 Correo\n"
        "🔑 Contraseña\n"
        "👤 Perfil\n"
        "📅 Fecha de vencimiento\n\n"
        "🛠️ Si tienes dudas, usa *Soporte*\n\n"
        f"💙 {MARCA}"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def informacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "ℹ️ *INFORMACIÓN DE LA TIENDA*\n\n"
        "*JHELIZCC VENTAS* es tu tienda digital para accesos de streaming.\n\n"
        "💎 Atención personalizada\n"
        "⚡ Entrega rápida\n"
        "🛠️ Soporte directo\n"
        "🔔 Avisos de vencimiento\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"💙 *Marca oficial*\n{MARCA}"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def soporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠️ *SOPORTE JHELIZCC VENTAS*\n\n"
        "Escríbenos el problema que tienes con tu cuenta o pedido.\n\n"
        "📌 Ejemplos:\n"
        "• No puedo ingresar\n"
        "• Me sale contraseña incorrecta\n"
        "• Mi perfil no aparece\n"
        "• Quiero renovar\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📩 Un administrador te responderá lo antes posible.\n\n"
        f"💙 {MARCA}",
        parse_mode="Markdown",
    )
    return WAITING_SUPPORT


async def renovar_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🔄 *RENOVACIÓN DE ACCESO*\n\n"
        "Si tu cuenta está por vencer o ya venció, escríbenos por soporte.\n\n"
        "También puedes responder a la notificación con:\n"
        "✅ Renovar\n"
        "❌ No renovar\n\n"
        f"💙 {MARCA}"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (update.message.text or "").strip()

    if texto == "🛍️ Ver catálogo":
        await catalogo(update, context)
        return MENU
    if texto == "💳 Comprar ahora":
        return await comprar_ahora(update, context)
    if texto == "📦 Mi pedido":
        await mis_pedidos(update, context)
        return MENU
    if texto == "🛠️ Soporte":
        return await soporte(update, context)
    if texto == "📘 Cómo comprar":
        await como_comprar(update, context)
        return MENU
    if texto == "ℹ️ Información":
        await informacion(update, context)
        return MENU
    if texto == "🔄 Renovar":
        await renovar_info(update, context)
        return MENU

    await update.message.reply_text("✨ Usa el menú para continuar.", parse_mode="Markdown")
    return MENU


async def platform_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_menu":
        await query.message.reply_text("⬅️ Volviste al menú.", reply_markup=main_menu_keyboard())
        return MENU

    _, key = query.data.split(":", 1)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT nombre, precio FROM productos WHERE clave = ?", (key,))
    item = cur.fetchone()
    conn.close()

    if not item:
        await query.message.reply_text("Producto no encontrado.")
        return MENU

    context.user_data["platform_name"] = item["nombre"]
    context.user_data["price"] = item["precio"]

    caption = (
        "🧾 *DETALLE DE TU PEDIDO*\n\n"
        f"📺 Plataforma: *{item['nombre']}*\n"
        f"💰 Precio: *S/ {item['precio']}*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "💳 *MÉTODO DE PAGO*\n\n"
        "Escanea el QR y realiza tu pago.\n"
        "Luego envía tu comprobante en este mismo chat.\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *Después de validar tu pago recibirás:*\n\n"
        "📧 Correo\n"
        "🔑 Contraseña\n"
        "👤 Perfil\n"
        "📅 Fecha de vencimiento\n\n"
        "💙 *JHELIZCC VENTAS*\n"
        f"{MARCA}"
    )

    if QR_PATH.exists():
        with QR_PATH.open("rb") as photo:
            await query.message.reply_photo(photo=photo, caption=caption, parse_mode="Markdown")
    else:
        await query.message.reply_text(caption, parse_mode="Markdown")

    return WAITING_PROOF


async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    platform_name = context.user_data.get("platform_name")
    price = context.user_data.get("price")

    if not platform_name:
        await update.message.reply_text(
            "Primero elige una plataforma desde *Comprar ahora*.",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown",
        )
        return MENU

    proof_text = "Sin detalle"
    proof_file_id = None
    if update.message.photo:
        proof_text = "Foto de comprobante enviada"
        proof_file_id = update.message.photo[-1].file_id
    elif update.message.text:
        proof_text = update.message.text.strip()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO pedidos (
            user_id, nombre, username, plataforma, precio, estado,
            comprobante, comprobante_file_id, fecha_creacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.id,
            user.full_name,
            user.username or "",
            platform_name,
            price,
            "pendiente",
            proof_text,
            proof_file_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    pedido_id = cur.lastrowid
    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ *Comprobante recibido correctamente*\n\n"
        "Tu pedido quedó registrado y será revisado por un administrador.\n\n"
        "📌 En breve te enviaremos:\n"
        "📧 Correo\n"
        "🔑 Contraseña\n"
        "👤 Perfil\n"
        "📅 Fecha de vencimiento\n\n"
        f"💙 Gracias por comprar en *JHELIZCC VENTAS*\n{MARCA}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )

    for admin_id in ADMIN_IDS:
        if proof_file_id:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=proof_file_id,
                caption=(
                    f"📥 Nuevo pedido #{pedido_id}\n"
                    f"Cliente: {user.full_name}\n"
                    f"Usuario: @{user.username or 'sin_username'}\n"
                    f"Plataforma: {platform_name}\n"
                    f"Precio: S/ {price}\n"
                    f"Estado: pendiente de verificar pago"
                ),
            )
        else:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"📥 Nuevo pedido #{pedido_id}\n"
                    f"Cliente: {user.full_name}\n"
                    f"Usuario: @{user.username or 'sin_username'}\n"
                    f"Plataforma: {platform_name}\n"
                    f"Precio: S/ {price}\n"
                    f"Comprobante: {proof_text}\n"
                    f"Estado: pendiente de verificar pago"
                ),
            )

    context.user_data.clear()
    return MENU


async def recibir_soporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mensaje = update.message.text

    texto_admin = (
        f"🛠 Nuevo mensaje de soporte\n\n"
        f"Cliente: {user.full_name}\n"
        f"Usuario: @{user.username or 'sin_username'}\n"
        f"ID: {user.id}\n\n"
        f"Mensaje:\n{mensaje}"
    )

    for admin_id in ADMIN_IDS:
        await context.bot.send_message(chat_id=admin_id, text=texto_admin)

    await update.message.reply_text(
        "✅ Tu mensaje fue enviado al soporte.\n"
        "Te responderemos pronto.",
        reply_markup=main_menu_keyboard(),
    )
    return MENU


async def mis_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, plataforma, estado, perfil_asignado, fecha_vencimiento
        FROM pedidos
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No tienes pedidos registrados.")
        return

    text = "📦 *Tus últimos pedidos:*\n\n"
    for row in rows:
        text += (
            f"#{row['id']} - {row['plataforma']}\n"
            f"Estado: {row['estado']}\n"
            f"Perfil: {row['perfil_asignado'] or '-'}\n"
            f"Vence: {row['fecha_vencimiento'] or '-'}\n\n"
        )

    await update.message.reply_text(text, parse_mode="Markdown")


# =========================
# ADMIN
# =========================
async def asignar_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("No autorizado.")
        return

    args = context.args
    if len(args) < 5:
        await update.message.reply_text(
            "Uso correcto:\n/asignar_manual ID correo contraseña perfil fecha"
        )
        return

    pedido_id = int(args[0])
    correo = args[1]
    password = args[2]
    perfil = args[3]
    fecha = args[4]

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, nombre, plataforma FROM pedidos WHERE id = ?", (pedido_id,))
    pedido = cur.fetchone()

    if not pedido:
        conn.close()
        await update.message.reply_text("Pedido no encontrado.")
        return

    user_id = pedido["user_id"]

    cur.execute(
        """
        UPDATE pedidos
        SET correo_asignado = ?, password_asignado = ?, perfil_asignado = ?,
            fecha_vencimiento = ?, estado = 'entregado'
        WHERE id = ?
        """,
        (correo, password, perfil, fecha, pedido_id),
    )

    cur.execute(
        """
        INSERT INTO asignaciones (
            pedido_id, cliente_user_id, cliente_nombre, plataforma,
            correo, perfil, fecha_vencimiento, estado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (pedido_id, user_id, pedido["nombre"], pedido["plataforma"], correo, perfil, fecha, "activo"),
    )

    conn.commit()
    conn.close()

    mensaje_cliente = (
        "🎉 *¡COMPRA CONFIRMADA!* 🎉\n\n"
        "Tu acceso ha sido activado correctamente.\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📺 Plataforma: *{pedido['plataforma']}*\n"
        f"📧 Correo: `{correo}`\n"
        f"🔑 Contraseña: `{password}`\n"
        f"👤 Perfil: *{perfil}*\n"
        f"📅 Vence: *{fecha}*\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ *Importante:*\n"
        "• Ingresa solo a tu perfil asignado\n"
        "• No cambies la contraseña\n"
        "• No elimines perfiles\n\n"
        "🛠️ Si tienes algún problema, usa *Soporte*\n\n"
        f"💙 Gracias por confiar en *JHELIZCC VENTAS*\n{MARCA}"
    )

    await context.bot.send_message(chat_id=user_id, text=mensaje_cliente, parse_mode="Markdown")
    await update.message.reply_text(f"✅ Cuenta enviada al cliente.\nPedido #{pedido_id}")


async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("No autorizado.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Uso correcto:\n/responder ID mensaje\n\n"
            "Ejemplo:\n/responder 8046525730 Hola, envíame tu correo para apoyarte."
        )
        return

    user_id = int(args[0])
    mensaje = " ".join(args[1:])

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🛠️ *Respuesta de soporte*\n\n{mensaje}\n\n💙 JHELIZCC VENTAS",
            parse_mode="Markdown",
        )
        await update.message.reply_text("✅ Respuesta enviada correctamente.")
    except Exception as e:
        await update.message.reply_text(f"No pude enviar el mensaje.\nError: {e}")


async def agregar_producto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("No autorizado.")
        return
    if len(context.args) < 3:
        await update.message.reply_text("Uso: /agregar_producto clave nombre precio")
        return

    clave = context.args[0].lower()
    nombre = context.args[1]
    precio = float(context.args[2])

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO productos (clave, nombre, precio) VALUES (?, ?, ?)", (clave, nombre, precio))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Producto agregado: {nombre} — S/{precio}")


async def editar_precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("No autorizado.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /editar_precio clave nuevo_precio")
        return

    clave = context.args[0].lower()
    nuevo_precio = float(context.args[1])

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE productos SET precio = ? WHERE clave = ?", (nuevo_precio, clave))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Precio actualizado: {clave} → S/{nuevo_precio}")


async def quitar_producto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("No autorizado.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /quitar_producto clave")
        return

    clave = context.args[0].lower()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM productos WHERE clave = ?", (clave,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Producto eliminado: {clave}")


async def clientes_por_producto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("No autorizado.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /clientes_por_producto producto")
        return

    producto = " ".join(context.args)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT cliente_nombre, correo, perfil, fecha_vencimiento
        FROM asignaciones
        WHERE lower(plataforma) = lower(?) AND estado = 'activo'
        ORDER BY id DESC
        """,
        (producto,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No encontré clientes para ese producto.")
        return

    texto = f"📺 *Clientes con {producto}:*\n\n"
    for row in rows:
        texto += (
            f"👤 {row['cliente_nombre']}\n"
            f"📧 {row['correo']}\n"
            f"🎭 {row['perfil']}\n"
            f"📅 {row['fecha_vencimiento']}\n\n"
        )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def buscar_correo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("No autorizado.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /buscar_correo correo")
        return

    correo = context.args[0]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT cliente_nombre, plataforma, perfil, fecha_vencimiento
        FROM asignaciones
        WHERE lower(correo) = lower(?) AND estado = 'activo'
        ORDER BY id DESC
        LIMIT 1
        """,
        (correo,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("No encontré ese correo asignado.")
        return

    texto = (
        f"📧 *Correo:* {correo}\n\n"
        f"👤 Cliente: {row['cliente_nombre']}\n"
        f"📺 Plataforma: {row['plataforma']}\n"
        f"🎭 Perfil: {row['perfil']}\n"
        f"📅 Vence: {row['fecha_vencimiento']}"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def anunciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("No autorizado.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /anunciar mensaje")
        return

    mensaje = " ".join(context.args)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_id FROM pedidos ORDER BY user_id ASC")
    usuarios = cur.fetchall()
    conn.close()

    enviados = 0
    fallidos = 0
    for row in usuarios:
        try:
            await context.bot.send_message(
                chat_id=row["user_id"],
                text=f"📢 *ANUNCIO JHELIZCC VENTAS*\n\n{mensaje}\n\n💙 {MARCA}",
                parse_mode="Markdown",
            )
            enviados += 1
        except Exception:
            fallidos += 1

    await update.message.reply_text(f"✅ Anuncio enviado.\nEnviados: {enviados}\nFallidos: {fallidos}")


# =========================
# MAIN
# =========================
def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_principal)],
            WAITING_PLATFORM: [CallbackQueryHandler(platform_selected)],
            WAITING_PROOF: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, receive_payment_proof)],
            WAITING_SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_soporte)],
            WAITING_SUPPORT_RESPONSE: [],
        },
        fallbacks=[CommandHandler("start", start)],
        per_user=True,
    )

    app.add_handler(conv)

    # Cliente
    app.add_handler(CommandHandler("vercatalogo", catalogo))
    app.add_handler(CommandHandler("comprarahora", comprar_ahora))
    app.add_handler(CommandHandler("comocomprar", como_comprar))
    app.add_handler(CommandHandler("informacion", informacion))
    app.add_handler(CommandHandler("soporte", soporte))
    app.add_handler(CommandHandler("mispedidos", mis_pedidos))
    app.add_handler(CommandHandler("renovar", renovar_info))

    # Admin
    app.add_handler(CommandHandler("asignar_manual", asignar_manual))
    app.add_handler(CommandHandler("responder", responder))
    app.add_handler(CommandHandler("agregar_producto", agregar_producto))
    app.add_handler(CommandHandler("editar_precio", editar_precio))
    app.add_handler(CommandHandler("quitar_producto", quitar_producto))
    app.add_handler(CommandHandler("clientes_por_producto", clientes_por_producto))
    app.add_handler(CommandHandler("buscar_correo", buscar_correo))
    app.add_handler(CommandHandler("anunciar", anunciar))

    app.run_polling()


if __name__ == "__main__":
    main()
