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

# =============================
# CONFIG
# =============================
# 👉 INSERISCI QUI IL TOKEN DEL TUO BOT TELEGRAM (per uso locale)
import os
TOKEN = os.environ.get("8563744998:AAEMDkCS1QLU_IfzPnpNlVJfeyWTe0U8MOc")
STACK_SIZE = 64

CATEGORIA, CIBO, STACK, TIPO_LISTA = range(4)


# =============================
# UTILS
# =============================

def format_stack(qta: int) -> str:
    """Ritorna 'X stack e Y' senza arrotondare per eccesso."""
    stack = qta // STACK_SIZE
    resto = qta % STACK_SIZE

    if stack > 0 and resto > 0:
        return f"{stack} stack e {resto}"
    elif stack > 0:
        return f"{stack} stack"
    else:
        return f"{resto}"


# =============================
# DATI MENU
# quantità riferite alla ricetta base
# =============================

MENU = {
    "Hamburger": {
        "Carne": {
            "emoji": "🍔🥩",
            "output": 6,
            "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di carne": 1, "Formaggio": 1},
        },
        "Vegani": {
            "emoji": "🍔🥬",
            "output": 6,
            "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger vegano": 1, "Formaggio": 1},
        },
        "Pesce": {
            "emoji": "🍔🐟",
            "output": 4,
            "ingredienti": {"Pane": 2, "Merluzzo": 1, "Salsa tartara": 1},
        },
        "Bacon": {
            "emoji": "🍔🥓",
            "output": 5,
            "ingredienti": {"Pane": 2, "Hamburger di carne": 1, "Bacon": 1, "Formaggio": 1},
        },
        "Pollo": {
            "emoji": "🍔🍗",
            "output": 6,
            "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di pollo": 1, "Formaggio": 1},
        },
    },
    "Wrap": {
        "Carne": {
            "emoji": "🌯🥩",
            "output": 5,
            "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di carne": 1, "Formaggio": 1},
        },
        "Vegani": {
            "emoji": "🌯🥬",
            "output": 5,
            "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger vegano": 1, "Formaggio": 1},
        },
        "Pesce": {
            "emoji": "🌯🐟",
            "output": 3,
            "ingredienti": {"Piadina": 1, "Merluzzo": 1, "Salsa tartara": 1},
        },
        "Bacon": {
            "emoji": "🌯🥓",
            "output": 4,
            "ingredienti": {"Piadina": 1, "Hamburger di carne": 1, "Bacon": 1, "Formaggio": 1},
        },
        "Pollo": {
            "emoji": "🌯🍗",
            "output": 5,
            "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di pollo": 1, "Formaggio": 1},
        },
    },
    "Tacos": {
        "Carne": {"emoji": "🌮🥩", "output": 4, "ingredienti": {"Piadina": 1, "Peperone rosso": 1, "Peperoncino": 1, "Hamburger di carne": 1, "Lattuga": 1/5}},
        "Pesce": {"emoji": "🌮🐟", "output": 4, "ingredienti": {"Piadina": 1, "Merluzzo": 1, "Peperoncino": 1, "Salsa tartara": 1}},
        "Piccanti": {"emoji": "🌮🔥", "output": 4, "ingredienti": {"Piadina": 1, "Hamburger di carne": 1, "Lattuga": 1/5, "Peperoncino": 1}},
        "Vegani": {"emoji": "🌮🥬", "output": 4, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Lattuga": 1/5, "Jalapeno": 1}},
    },
    "HotDog": {
        "Normali": {"emoji": "🌭", "output": 4, "ingredienti": {"Pane": 1, "Wurstel": 1, "Ketchup": 1, "Maionese": 1}},
        "Cipolla croccante": {"emoji": "🌭🧅", "output": 4, "ingredienti": {"Pane": 1, "Wurstel": 1, "Cipolla": 1, "Senape": 1}},
        "Vegani": {"emoji": "🌭🥬", "output": 4, "ingredienti": {"Pane": 1, "Wurstel vegano": 1, "Pomodoro": 1/5, "Lattuga": 1/5}},
    },
    "Extra": {
        "Patatine": {"emoji": "🍟", "output": 4, "ingredienti": {"Patate": 4}},
        "Nuggets": {"emoji": "🍗", "output": 12, "ingredienti": {"Pollo": 6, "Pastella": 6}},
        "TastyBasket": {"emoji": "🧺", "output": 6, "ingredienti": {"Nuggets": 3, "Sale": 1, "Maionese": 1, "Ketchup": 1}},
    },
}


# =============================
# START
# =============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"🍔 {cat}", callback_data=f"cat|{cat}")]
        for cat in MENU.keys()
    ]

    await update.message.reply_text(
        "Scegli una categoria:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CATEGORIA


# =============================
# SCELTA CATEGORIA
# =============================

async def scelta_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    categoria = query.data.split("|")[1]
    context.user_data["categoria"] = categoria

    keyboard = []
    for nome, dati in MENU[categoria].items():
        keyboard.append([
            InlineKeyboardButton(
                f"{dati['emoji']} {nome}",
                callback_data=f"cibo|{nome}",
            )
        ])

    keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data="back")])

    await query.edit_message_text(
        f"Categoria: *{categoria}*\nScegli il cibo:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CIBO


# =============================
# TORNA INDIETRO
# =============================

async def indietro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await start(query, context)


# =============================
# SCELTA CIBO
# =============================

async def scelta_cibo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["cibo"] = query.data.split("|")[1]

    await query.edit_message_text("Quanti stack vuoi craftare?")
    return STACK


# =============================
# INSERIMENTO STACK
# =============================

async def inserisci_stack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stack = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Inserisci un numero valido.")
        return STACK

    context.user_data["stack"] = stack

    keyboard = [
        [InlineKeyboardButton("📦 Lista unica ingredienti", callback_data="lista|unica")],
        [InlineKeyboardButton("📄 Lista separata", callback_data="lista|separata")],
    ]

    await update.message.reply_text(
        "Come vuoi visualizzare gli ingredienti?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return TIPO_LISTA


# =============================
# CALCOLO INGREDIENTI
# =============================

async def calcola(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tipo_lista = query.data.split("|")[1]

    categoria = context.user_data["categoria"]
    cibo = context.user_data["cibo"]
    stack = context.user_data["stack"]

    dati = MENU[categoria][cibo]

    totale_output = stack * STACK_SIZE
    moltiplicatore = totale_output / dati["output"]

    # inizializza lista cumulativa
    if "lista_totale" not in context.user_data:
        context.user_data["lista_totale"] = defaultdict(float)

    ingredienti_totali = context.user_data["lista_totale"]

    for nome, qta in dati["ingredienti"].items():
        ingredienti_totali[nome] += qta * moltiplicatore

    # salva che siamo almeno al secondo cibo
    count = context.user_data.get("count_cibi", 0) + 1
    context.user_data["count_cibi"] = count

    testo = "🧾 *Lista ingredienti attuale:*\n\n"
    for nome, qta in ingredienti_totali.items():
        testo += f"- {nome}: {format_stack(math.ceil(qta))}\n"

    # tastiera dopo il primo cibo
    if count >= 2:
        keyboard = [
            [InlineKeyboardButton("➕ Aggiungi altro cibo", callback_data="continua")],
            [InlineKeyboardButton("✅ Conferma lista", callback_data="conferma")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("➕ Aggiungi altro cibo", callback_data="continua")],
        ]

    await query.edit_message_text(
        testo,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CATEGORIA


async def continua_scelta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ritorna al menu categorie mantenendo la lista cumulativa."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(f"🍔 {cat}", callback_data=f"cat|{cat}")]
        for cat in MENU.keys()
    ]

    await query.edit_message_text(
        "Scegli un altro cibo da aggiungere:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CATEGORIA


async def conferma_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra la lista finale e termina."""
    query = update.callback_query
    await query.answer()

    ingredienti_totali = context.user_data.get("lista_totale", {})

    testo = "✅ *Lista finale ingredienti:*\n\n"
    for nome, qta in ingredienti_totali.items():
        testo += f"- {nome}: {format_stack(math.ceil(qta))}\n"

    await query.edit_message_text(testo, parse_mode="Markdown")

    # reset dati utente
    context.user_data.clear()

    return ConversationHandler.END


# =============================
# MAIN
# =============================


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORIA: [CallbackQueryHandler(scelta_categoria, pattern="^cat\\|")],
            CIBO: [
                CallbackQueryHandler(scelta_cibo, pattern="^cibo\\|"),
                CallbackQueryHandler(indietro, pattern="^back$"),
            ],
            STACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_stack)],
            TIPO_LISTA: [CallbackQueryHandler(calcola, pattern="^lista\\|")],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(continua_scelta, pattern="^continua$"))
    app.add_handler(CallbackQueryHandler(conferma_lista, pattern="^conferma$"))

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

