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

# =============================
# CONFIG
# =============================
TOKEN = os.environ.get("TOKEN")
STACK_SIZE = 64

CATEGORIA, CIBO, STACK, NOME_DIP, NOME_CAPO = range(5)


# =============================
# UTILS
# =============================

def format_stack(qta: int) -> str:
    stack = qta // STACK_SIZE
    resto = qta % STACK_SIZE

    if stack > 0 and resto > 0:
        return f"{stack} stack e {resto}"
    elif stack > 0:
        return f"{stack} stack"
    else:
        return f"{resto}"


# =============================
# MENU DATI
# =============================

MENU = {
    "Hamburger": {
        "Carne": {"emoji": "🍔🥩", "output": 6, "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di carne": 1, "Formaggio": 1}},
        "Vegani": {"emoji": "🍔🥬", "output": 6, "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger vegano": 1, "Formaggio": 1}},
        "Pesce": {"emoji": "🍔🐟", "output": 4, "ingredienti": {"Pane": 2, "Merluzzo": 1, "Cipolla": 1, "Cetriolo": 1/4, "Maionese": 1}},
        "Bacon": {"emoji": "🍔🥓", "output": 5, "ingredienti": {"Pane": 2, "Hamburger di carne": 1, "Bacon": 1, "Formaggio": 1}},
        "Pollo": {"emoji": "🍔🍗", "output": 6, "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di pollo": 1, "Formaggio": 1}},
    },
    "Wrap": {
        "Carne": {"emoji": "🌯🥩", "output": 5, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di carne": 1, "Formaggio": 1}},
        "Vegani": {"emoji": "🌯🥬", "output": 5, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger vegano": 1, "Formaggio": 1}},
        "Pesce": {"emoji": "🌯🐟", "output": 3, "ingredienti": {"Piadina": 1, "Merluzzo": 1, "Cipolla": 1, "Cetriolo": 1/4, "Maionese": 1}},
        "Bacon": {"emoji": "🌯🥓", "output": 4, "ingredienti": {"Piadina": 1, "Hamburger di carne": 1, "Bacon": 1, "Formaggio": 1}},
        "Pollo": {"emoji": "🌯🍗", "output": 5, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di pollo": 1, "Formaggio": 1}},
    },
    "Tacos": {
        "Carne": {"emoji": "🌮🥩", "output": 4, "ingredienti": {"Piadina": 1, "Peperone rosso": 1, "Peperoncino": 1, "Hamburger di carne": 1, "Lattuga": 1/5}},
        "Pesce": {"emoji": "🌮🐟", "output": 4, "ingredienti": {"Piadina": 1, "Merluzzo": 1, "Peperoncino": 1, "Cipolla": 1, "Cetriolo": 1/4, "Maionese": 1}},
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
        "TastyBasket": {"emoji": "🧺", "output": 6, "ingredienti": {"Pollo": 3, "Pastella": 3, "Sale": 1, "Maionese": 1, "Ketchup": 1}},
    },
}


# =============================
# START
# =============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [[InlineKeyboardButton(f"🍽️ {cat}", callback_data=f"cat|{cat}")] for cat in MENU.keys()]

    await update.message.reply_text("Scegli una categoria:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CATEGORIA


async def scelta_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    categoria = query.data.split("|")[1]
    context.user_data["categoria"] = categoria

    keyboard = [
        [InlineKeyboardButton(f"{dati['emoji']} {nome}", callback_data=f"cibo|{nome}")]
        for nome, dati in MENU[categoria].items()
    ]
    keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data="back")])

    await query.edit_message_text(f"Categoria: *{categoria}*\nScegli il cibo:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return CIBO


async def indietro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await start(query, context)


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

    categoria = context.user_data["categoria"]
    cibo = context.user_data["cibo"]

    dati = MENU[categoria][cibo]
    totale_output = stack * STACK_SIZE
    moltiplicatore = totale_output / dati["output"]

    if "lista_totale" not in context.user_data:
        context.user_data["lista_totale"] = defaultdict(float)
        context.user_data["cibi_scelti"] = []

    for nome, qta in dati["ingredienti"].items():
        context.user_data["lista_totale"][nome] += qta * moltiplicatore

    context.user_data["cibi_scelti"].append((categoria, cibo, stack))

    keyboard = [
        [InlineKeyboardButton("➕ Aggiungi altro cibo", callback_data="continua")],
        [InlineKeyboardButton("🗑️ Reset lista", callback_data="reset")],
        [InlineKeyboardButton("✅ Conferma lista", callback_data="conferma")],
    ]

    await update.message.reply_text("Cibo aggiunto alla lista.", reply_markup=InlineKeyboardMarkup(keyboard))
    return CATEGORIA


async def continua_scelta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton(f"🍽️ {cat}", callback_data=f"cat|{cat}")] for cat in MENU.keys()]

    await query.edit_message_text("Scegli un altro cibo:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CATEGORIA


async def reset_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    await query.edit_message_text("Lista resettata. Usa /start per ricominciare.")
    return ConversationHandler.END


async def conferma_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ingredienti_totali = context.user_data.get("lista_totale", {})

    testo = "🧾 *Ingredienti necessari:*\n\n"
    for nome, qta in ingredienti_totali.items():
        testo += f"- {nome}: {format_stack(math.ceil(qta))}\n"

    testo += "\n👤 Scrivi il nome del *dipendente incaricato*:"

    await query.edit_message_text(testo, parse_mode="Markdown")
    return NOME_DIP


async def salva_nome_dip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome_dip"] = update.message.text.strip()
    await update.message.reply_text("✍️ Scrivi il nome di chi assegna l'incarico:")
    return NOME_CAPO


async def genera_incarico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome_capo = update.message.text.strip()
    nome_lower = nome_capo.lower()

    ruoli = {
        "blackshade15": "Direttrice",
        "andrygamer06": "Vice Dir.",
        "mrsh0t_": "Capocuoco",
    }

    if nome_lower not in ruoli:
        await update.message.reply_text("Non hai i permessi necessari!")
        context.user_data.clear()
        return ConversationHandler.END

    ruolo = ruoli[nome_lower]
    nome_dip = context.user_data["nome_dip"]

    now = datetime.now()
    giorni = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    giorno = giorni[now.weekday()]
    data = now.strftime("%d/%m/%Y")

    testo = f"📋 *Incarico*\n{giorno} {data}\n--------------------------------\n-Preparare:\n"

    for categoria, cibo, stack in context.user_data["cibi_scelti"]:
        testo += f"- {stack} stack di {categoria} {cibo}\n"

    testo += (
        "\nAl completamento dell'incarico assegnato è richiesta la controfirma di questo libro.\n"
        f"-Dipendente incaricato: {nome_dip}\n\n"
        f"-Firma {ruolo}: {nome_capo}"
    )

    await update.message.reply_text(testo, parse_mode="Markdown")

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
            CATEGORIA: [
                CallbackQueryHandler(scelta_categoria, pattern="^cat\\|"),
                CallbackQueryHandler(continua_scelta, pattern="^continua$"),
                CallbackQueryHandler(conferma_lista, pattern="^conferma$"),
                CallbackQueryHandler(reset_lista, pattern="^reset$"),
            ],
            CIBO: [
                CallbackQueryHandler(scelta_cibo, pattern="^cibo\\|"),
                CallbackQueryHandler(indietro, pattern="^back$"),
            ],
            STACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_stack)
            ],
            NOME_DIP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, salva_nome_dip)
            ],
            NOME_CAPO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, genera_incarico)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)

    print("Bot avviato in polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
