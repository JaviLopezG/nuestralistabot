import os
import json
import sqlite3
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Configuración básica de logs para ver errores en docker logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DB_FILE = "/data/lists.db"

def init_db():
    """Inicializa la base de datos SQLite si no existe."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                chat_id INTEGER PRIMARY KEY,
                items TEXT
            )
        """)

def get_items(chat_id):
    """Recupera la lista de items como array."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT items FROM lists WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else []

def save_items(chat_id, items):
    """Guarda la lista de items como JSON string."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO lists (chat_id, items) VALUES (?, ?)", 
                     (chat_id, json.dumps(items)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola. Usa /add, /del, /lista o /reset.")

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    items = get_items(chat_id)
    
    if not items:
        await update.message.reply_text("La lista está vacía.")
        return

    msg = "📋 **Lista actual:**\n"
    for idx, item in enumerate(items, 1):
        msg += f"{idx}. {item}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Uso: /add <texto del elemento>")
        return

    chat_id = update.effective_chat.id
    items = get_items(chat_id)
    items.append(text)
    save_items(chat_id, items)
    
    await update.message.reply_text(f"✅ Añadido: {text}")

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(context.args[0]) - 1 # Usuario ve 1-based, array es 0-based
    except (IndexError, ValueError):
        await update.message.reply_text("Uso: /del <número de la lista>")
        return

    chat_id = update.effective_chat.id
    items = get_items(chat_id)

    if 0 <= idx < len(items):
        removed = items.pop(idx)
        save_items(chat_id, items)
        await update.message.reply_text(f"🗑 Eliminado: {removed}")
    else:
        await update.message.reply_text("❌ Número inválido.")

async def reset_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Uso: /reset <item1>, <item2>, ...")
        return

    # Separa por comas y limpia espacios
    new_items = [x.strip() for x in text.split(',') if x.strip()]
    
    chat_id = update.effective_chat.id
    save_items(chat_id, new_items)
    
    await update.message.reply_text(f"🔄 Lista reemplazada con {len(new_items)} elementos.")

if __name__ == '__main__':
    # Lee el token de variable de entorno
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No se encontró la variable TELEGRAM_TOKEN")

    init_db()
    
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("lista", show_list))
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("del", delete_item))
    application.add_handler(CommandHandler("reset", reset_list))

    print("Bot iniciado...")
    application.run_polling()
