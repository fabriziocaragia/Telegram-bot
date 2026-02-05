# Codice aggiornato con incarico finale corretto + reset lista
import os
import math
from collections import defaultdict
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

TOKEN = os.environ.get("TOKEN")
STACK_SIZE = 64

CATEGORIA, CIBO, STACK, NOME_DIP, NOME_DIR = range(5)


def format_stack(qta: int) -> str:
    stack = qta // STACK_SIZE
    resto = qta % STACK_SIZE

    if stack > 0 and resto > 0:
        return f"{stack} stack e {resto}"
    elif stack > 0:
        return f"{stack} stack"
    else:
        return f"{resto}"


def espandi_ingredienti(ingredienti):
    nuovi = defaultdict(float)

    for nome, qta in ingredienti.items():
        if nome == "Salsa tartara":
            nuovi["Cipolla"] += 1 * qta
            nuovi["Cetriolo"] += (1 / 4) * qta
            nuovi["Maionese"] += 1 * qta
        else:
            nuovi[nome] += qta

    return nuovi


MENU = {
    "Hamburger": {
        "emoji": "🍔",
        "cibi": {
            "Carne": {"emoji": "🥩", "output": 6, "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di carne": 1, "Formaggio": 1}},
            "Vegani": {"emoji": "🥬", "output": 6, "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger vegano": 1, "Formaggio": 1}},
            "Pesce": {"emoji": "🐟", "output": 4, "ingredienti": {"Pane": 2, "Merluzzo": 1, "Salsa tartara": 1}},
            "Bacon": {"emoji": "🥓", "output": 5, "ingredienti": {"Pane": 2, "Hamburger di carne": 1, "Bacon": 1, "Formaggio": 1}},
            "Pollo": {"emoji": "🍗", "output": 6, "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di pollo": 1, "Formaggio": 1}},
        },
    },
    "Wrap": {
        "emoji": "🌯",
        "cibi": {
            "Carne": {"emoji": "🥩", "output": 5, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di carne": 1, "Formaggio": 1}},
            "Vegani": {"emoji": "🥬", "output": 5, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger vegano": 1, "Formaggio": 1}},
            "Pesce": {"emoji": "🐟", "output": 3, "ingredienti": {"Piadina": 1, "Merluzzo": 1, "Salsa tartara": 1}},
            "Bacon": {"emoji": "🥓", "output": 4, "ingredienti": {"Piadina": 1, "Hamburger di carne": 1, "Bacon": 1, "Formaggio": 1}},
            "Pollo": {"emoji": "🍗", "output": 5, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di pollo": 1, "Formaggio": 1}},
        },
    },
    "Tacos": {
        "emoji": "🌮",
        "cibi": {
            "Carne": {"emoji": "🥩", "output": 4, "ingredienti": {"Piadina": 1, "Peperone rosso": 1, "Peperoncino": 1, "Hamburger di carne": 1, "Lattuga": 1/5}},
            "Pesce": {"emoji": "🐟", "output": 4, "ingredienti": {"Piadina": 1, "Merluzzo": 1, "Peperoncino": 1, "Salsa tartara": 1}},
            "Piccanti": {"emoji": "🔥", "output": 4, "ingredienti": {"Piadina": 1, "Hamburger di carne": 1, "Lattuga": 1/5, "Peperoncino": 1}},
            "Vegani": {"emoji": "🥬", "output": 4, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Lattuga": 1/5, "Jalapeno": 1}},
        },
    },
    "HotDog": {
        "emoji": "🌭",
        "cibi": {
            "Normali": {"emoji": "🌭", "output": 4, "ingredienti": {"Pane": 1, "Wurstel": 1, "Ketchup": 1, "Maionese": 1}},
            "Cipolla croccante": {"emoji": "🧅", "output": 4, "ingredienti": {"Pane": 1, "Wurstel": 1, "Cipolla": 1, "Senape": 1}},
            "Vegani": {"emoji": "🥬", "output": 4, "ingredienti": {"Pane": 1, "Wurstel vegano": 1, "Pomodoro": 1/5, "Lattuga": 1/5}},
        },
    },
    "Extra": {
        "emoji": "🧺",
        "cibi": {
            "Patatine": {"emoji": "🍟", "output": 4, "ingredienti": {"Patate": 4}},
            "Nuggets": {"emoji": "🍗", "output": 12, "ingredienti": {"Pollo": 6, "Pastella": 6}},
            "TastyBasket": {"emoji": "🧺", "output": 6, "ingredienti": {"Nuggets": 3, "Sale": 1, "Maionese": 1, "Ketchup": 1}},
        },
    },
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton(f"{dati['emoji']} {cat}", callback_data=f"cat|{cat}")]
        for cat, dati in MENU.items()
    ]

    await update.message.reply_text(
        "Scegli una categoria:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CATEGORIA


async def scelta_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    categoria = query.data.split("|")[1]
    context.user_data["categoria"] = categoria

    keyboard = []
    for nome, dati in MENU[categoria]["cibi"].items():
        keyboard.append([
            InlineKeyboardButton(f"{dati['emoji']} {nome}", callback_data=f"cibo|{nome}")
        ])

    await query.edit_message_text(
        f"Categoria: *{categoria}*\nScegli il cibo:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CIBO


async def scelta_cibo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["cibo"] = query.data.split("|")[1]

    await query.edit_message_text("Quanti stack vuoi craftare?")
    return STACK


async def inserisci_stack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stack = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Inserisci un numero valido.")
        return STACK

    context.user_data["stack"] = stack

    return await calcola(update, context)


async def calcola(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categoria = context.user_data["categoria"]
    cibo = context.user_data["cibo"]
    stack = context.user_data["stack"]

    dati = MENU[categoria]["cibi"][cibo]

    if "lista_totale" not in context.user_data:
        context.user_data["lista_totale"] = defaultdict(float)
        context.user_data["cibi_scelti"] = []

    context.user_data["cibi_scelti"].append((categoria, cibo, stack))

    keyboard = [
        [InlineKeyboardButton("➕ Aggiungi altro cibo", callback_data="continua")],
        [InlineKeyboardButton("🗑 Reset lista", callback_data="reset")],
        [InlineKeyboardButton("✅ Conferma lista", callback_data="conferma")],
    ]

    testo = "Cibo aggiunto alla lista."

    if update.callback_query:
        await update.callback_query.edit_message_text(testo, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(testo, reply_markup=InlineKeyboardMarkup(keyboard))

    return CATEGORIA


async def reset_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    await query.edit_message_text("Lista resettata. Usa /start per ricominciare.")
    return ConversationHandler.END


async def continua_scelta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(f"{dati['emoji']} {cat}", callback_data=f"cat|{cat}")]
        for cat, dati in MENU.items()
    ]

    await query.edit_message_text("Scegli un altro cibo da aggiungere:", reply_markup=InlineKeyboardMarkup(keyboard))

    return CATEGORIA


async def conferma_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("Nome dipendente incaricato?")
    return NOME_DIP


async def nome_dipendente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome_dip"] = update.message.text
    await update.message.reply_text("Nome di chi assegna l'incarico?")
    return NOME_DIR


async def nome_direttore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome_dir = update.message.text

    ruoli = {
        "BlackShade15": "Direttrice",
        "Andrygamer06": "Vice Dir.",
        "MrSh0t_": "Capocuoco",
    }

    ruolo = ruoli.get(nome_dir)

    if not ruolo:
        await update.message.reply_text("Non hai i permessi necessari!")
        context.user_data.clear()
        return ConversationHandler.END

    nome_dip = context.user_data["nome_dip"]
    cibi = context.user_data.get("cibi_scelti", [])

    giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    now = datetime.now()
    data_str = f"{giorni[now.weekday()]} {now.strftime('%d/%m/%Y')}"

    testo = "📖 *Incarico*\n"
    testo += f"{data_str}\n"
    testo += "--------------------------------\n"
    testo += "- Preparare:\n"

    for categoria, cibo, stack in cibi:
        testo += f"  - {stack} stack di {categoria} {cibo}\n"

    testo += "\nAl completamento dell'incarico assegnato è richiesta la controfirma di questo libro.\n"
    testo += f"- Dipendente incaricato: {nome_dip}\n"
    testo += f"- Firma {ruolo}: {nome_dir}"

    await update.message.reply_text(testo, parse_mode="Markdown")

    context.user_data.clear()
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORIA: [
                CallbackQueryHandler(scelta_categoria, pattern="^cat\\|"),
                CallbackQueryHandler(continua_scelta, pattern="^continua$"),
                CallbackQueryHandler(conferma_lista, pattern="^conferma$"),
                CallbackQueryHandler(reset_lista, pattern="^reset$"),
            ],
            CIBO: [CallbackQueryHandler(scelta_cibo, pattern="^cibo\\|")],
            STACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_stack)],
            NOME_DIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, nome_dipendente)],
            NOME_DIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, nome_direttore)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)

    if os.environ.get("RENDER_EXTERNAL_URL"):
        PORT = int(os.environ.get("PORT", 10000))
        WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")

        app.run_webhook(listen="0.0.0.0", port=PORT, webhook_url=WEBHOOK_URL)
    else:
        app.run_polling()


if __name__ == "__main__":
    main()
