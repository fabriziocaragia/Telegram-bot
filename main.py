import os
import math
from collections import defaultdict

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

CATEGORIA, CIBO, STACK = range(3)


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
    """Scompone la salsa tartara nei singoli ingredienti."""
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
        "emoji": "🍟",
        "cibi": {
            "Patatine": {"emoji": "🍟", "output": 4, "ingredienti": {"Patate": 4}},
            "Nuggets": {"emoji": "🍗", "output": 12, "ingredienti": {"Pollo": 6, "Pastella": 6}},
            "TastyBasket": {"emoji": "🧺", "output": 6, "ingredienti": {"Nuggets": 3, "Sale": 1, "Maionese": 1, "Ketchup": 1}},
        },
    },
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            InlineKeyboardButton(
                f"{dati['emoji']} {nome}",
                callback_data=f"cibo|{nome}",
            )
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

    totale_output = stack * STACK_SIZE
    moltiplicatore = totale_output / dati["output"]

    if "lista_totale" not in context.user_data:
        context.user_data["lista_totale"] = defaultdict(float)

    ingredienti_totali = context.user_data["lista_totale"]

    ingredienti_base = espandi_ingredienti(dati["ingredienti"])

    for nome, qta in ingredienti_base.items():
        ingredienti_totali[nome] += qta * moltiplicatore

    count = context.user_data.get("count_cibi", 0) + 1
    context.user_data["count_cibi"] = count

    testo = "🧾 *Lista ingredienti attuale:*\n\n"
    for nome, qta in ingredienti_totali.items():
        testo += f"- {nome}: {format_stack(math.ceil(qta))}\n"

    if count >= 2:
        keyboard = [
            [InlineKeyboardButton("➕ Aggiungi altro cibo", callback_data="continua")],
            [InlineKeyboardButton("✅ Conferma lista", callback_data="conferma")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("➕ Aggiungi altro cibo", callback_data="continua")],
        ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            testo,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.message.reply_text(
            testo,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    return CATEGORIA


async def continua_scelta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(f"{dati['emoji']} {cat}", callback_data=f"cat|{cat}")]
        for cat, dati in MENU.items()
    ]

    await query.edit_message_text(
        "Scegli un altro cibo da aggiungere:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CATEGORIA


async def conferma_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ingredienti_totali = context.user_data.get("lista_totale", {})

    testo = "✅ *Lista finale ingredienti:*\n\n"
    for nome, qta in ingredienti_totali.items():
        testo += f"- {nome}: {format_stack(math.ceil(qta))}\n"

    await query.edit_message_text(testo, parse_mode="Markdown")

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
            ],
            CIBO: [CallbackQueryHandler(scelta_cibo, pattern="^cibo\\|")],
            STACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_stack)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)

    PORT = int(os.environ.get("PORT", 10000))
    WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")

    print("Bot avviato in modalità WEBHOOK...")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
    )


if __name__ == "__main__":
    main()
