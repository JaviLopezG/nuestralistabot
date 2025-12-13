import os
import json
import sqlite3
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DB_FILE = "/data/lists.db"

def init_db():
    """Inicializa la DB con soporte para múltiples listas por chat."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                chat_id INTEGER,
                name TEXT,
                items TEXT,
                PRIMARY KEY (chat_id, name)
            )
        """)

def get_list_content(chat_id, list_name):
    """Devuelve los items de una lista específica o None si no existe."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute(
            "SELECT items FROM lists WHERE chat_id = ? AND name = ?", 
            (chat_id, list_name.lower())
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

def save_list_content(chat_id, list_name, items):
    """Guarda o actualiza el contenido de una lista."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO lists (chat_id, name, items) VALUES (?, ?, ?)", 
            (chat_id, list_name.lower(), json.dumps(items))
        )

def delete_list_db(chat_id, list_name):
    """Borra una lista entera de la DB."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute(
            "DELETE FROM lists WHERE chat_id = ? AND name = ?", 
            (chat_id, list_name.lower())
        )
        return cursor.rowcount > 0

def get_all_lists(chat_id):
    """Devuelve los nombres de todas las listas del chat."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT name FROM lists WHERE chat_id = ?", (chat_id,))
        return [row[0] for row in cursor.fetchall()]

# --- Comandos ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 **Gestor de Listas 2.0**\n\n"
        "Comandos:\n"
        "`/mklist <nombre>` - Crea una lista nueva\n"
        "`/rmlist <nombre>` - Borra una lista entera\n"
        "`/lists` - Ver todas las listas creadas\n"
        "`/show <nombre>` - Ver contenido de una lista\n"
        "`/add <nombre> <item>` - Añadir a una lista\n"
        "`/del <nombre> <numero>` - Borrar item por número\n"
        "`/reset <nombre> <i1, i2...>` - Sobrescribir lista"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def create_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /mklist <nombre_lista>")
        return
    
    name = context.args[0]
    chat_id = update.effective_chat.id
    
    if get_list_content(chat_id, name) is not None:
        await update.message.reply_text(f"⚠️ La lista '{name}' ya existe.")
    else:
        save_list_content(chat_id, name, [])
        await update.message.reply_text(f"✅ Lista '{name}' creada.")

async def remove_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /rmlist <nombre_lista>")
        return

    name = context.args[0]
    if delete_list_db(update.effective_chat.id, name):
        await update.message.reply_text(f"🗑 Lista '{name}' eliminada por completo.")
    else:
        await update.message.reply_text(f"❌ La lista '{name}' no existe.")

async def show_all_lists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lists = get_all_lists(update.effective_chat.id)
    if not lists:
        await update.message.reply_text("📭 No hay listas creadas. Usa /mklist <nombre>.")
        return
    
    msg = "📂 **Listas disponibles:**\n" + "\n".join(f"- {l}" for l in lists)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def show_list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /show <nombre_lista>")
        return

    name = context.args[0]
    items = get_list_content(update.effective_chat.id, name)
    
    if items is None:
        await update.message.reply_text(f"❌ La lista '{name}' no existe.")
        return
    if not items:
        await update.message.reply_text(f"📂 La lista '{name}' está vacía.")
        return

    msg = f"📋 **{name.upper()}:**\n"
    for idx, item in enumerate(items, 1):
        msg += f"{idx}. {item}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /add <nombre_lista> <texto>")
        return

    name = context.args[0]
    text = ' '.join(context.args[1:])
    chat_id = update.effective_chat.id
    items = get_list_content(chat_id, name)

    if items is None:
        await update.message.reply_text(f"❌ La lista '{name}' no existe. Créala con /mklist.")
        return

    items.append(text)
    save_list_content(chat_id, name, items)
    await update.message.reply_text(f"✅ Añadido a '{name}': {text}")

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /del <nombre_lista> <número>")
        return

    name = context.args[0]
    try:
        idx = int(context.args[1]) - 1
    except ValueError:
        await update.message.reply_text("El segundo argumento debe ser un número.")
        return

    chat_id = update.effective_chat.id
    items = get_list_content(chat_id, name)

    if items is None:
        await update.message.reply_text(f"❌ La lista '{name}' no existe.")
        return

    if 0 <= idx < len(items):
        removed = items.pop(idx)
        save_list_content(chat_id, name, items)
        await update.message.reply_text(f"🗑 Eliminado de '{name}': {removed}")
    else:
        await update.message.reply_text("❌ Número inválido.")

async def reset_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /reset <nombre_lista> <item1, item2...>")
        return

    name = context.args[0]
    text = ' '.join(context.args[1:])
    chat_id = update.effective_chat.id
    
    # Verificamos si existe antes de resetear
    if get_list_content(chat_id, name) is None:
        await update.message.reply_text(f"❌ La lista '{name}' no existe.")
        return

    new_items = [x.strip() for x in text.split(',') if x.strip()]
    save_list_content(chat_id, name, new_items)
    await update.message.reply_text(f"🔄 Lista '{name}' reemplazada con {len(new_items)} elementos.")

if __name__ == '__main__':
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No se encontró la variable TELEGRAM_TOKEN")

    init_db()
    
    app = ApplicationBuilder().token(token).build()

    # Mapeo de comandos
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("mklist", create_list))
    app.add_handler(CommandHandler("rmlist", remove_list))
    app.add_handler(CommandHandler("lists", show_all_lists))
    app.add_handler(CommandHandler("show", show_list_items))
    app.add_handler(CommandHandler("add", add_item))
    app.add_handler(CommandHandler("del", delete_item))
    app.add_handler(CommandHandler("reset", reset_list))

    print("Bot Multilista iniciado...")
    app.run_polling()
