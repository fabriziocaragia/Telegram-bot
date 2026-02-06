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

CATEGORIA, CIBO, STACK, CONFERMA, NOME_DIP, NOME_CAPO = range(6)


def format_stack(qta: int) -> str:
    stack = qta // STACK_SIZE
    resto = qta % STACK_SIZE

    if stack > 0 and resto > 0:
        return f"{stack} stack e {resto}"
    elif stack > 0:
        return f"{stack} stack"
    else:
        return f"{resto}"


MENU = {
    "Hamburger": {
        "Carne": {"emoji": "🍔🥩", "output": 6, "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di carne": 1, "Formaggio": 1}},
        "Vegani": {"emoji": "🍔🥬", "output": 6, "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger vegano": 1, "Formaggio": 1}},
        "Pesce": {"emoji": "🍔🐟", "output": 4, "ingredienti": {"Pane": 2, "Merluzzo": 1, "Salsa tartara": 1}},
        "Bacon": {"emoji": "🍔🥓", "output": 5, "ingredienti": {"Pane": 2, "Hamburger di carne": 1, "Bacon": 1, "Formaggio": 1}},
        "Pollo": {"emoji": "🍔🍗", "output": 6, "ingredienti": {"Pane": 2, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di pollo": 1, "Formaggio": 1}},
    },
    "Wrap": {
        "Carne": {"emoji": "🌯🥩", "output": 5, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di carne": 1, "Formaggio": 1}},
        "Vegani": {"emoji": "🌯🥬", "output": 5, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger vegano": 1, "Formaggio": 1}},
        "Pesce": {"emoji": "🌯🐟", "output": 3, "ingredienti": {"Piadina": 1, "Merluzzo": 1, "Salsa tartara": 1}},
        "Bacon": {"emoji": "🌯🥓", "output": 4, "ingredienti": {"Piadina": 1, "Hamburger di carne": 1, "Bacon": 1, "Formaggio": 1}},
        "Pollo": {"emoji": "🌯🍗", "output": 5, "ingredienti": {"Piadina": 1, "Pomodoro": 1/5, "Insalata": 1/5, "Hamburger di pollo": 1, "Formaggio": 1}},
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


# ================= START (emoji corrette nel primo menu) =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emoji_categoria = {
        "Hamburger": "🍔",
        "Wrap": "🌯",
        "Tacos": "🌮",
        "HotDog": "🌭",
        "Extra": "🍟",
    }

    keyboard = [
        [InlineKeyboardButton(f"{emoji_categoria.get(cat, '🍽️')} {cat}", callback_data=f"cat|{cat}")]
        for cat in MENU.keys()
    ]

    await update.message.reply_text(
        "Scegli una categoria:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CATEGORIA
# ========================================================================


async def scelta_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    categoria = query.data.split("|")[1]
    context.user_data["categoria"] = categoria

    keyboard = [
        [InlineKeyboardButton(f"{d['emoji']} {nome}", callback_data=f"cibo|{nome}")]
        for nome, d in MENU[categoria].items()
    ]
    keyboard.append([InlineKeyboardButton("🔄 Reset lista", callback_data="reset")])

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

    categoria = context.user_data["categoria"]
    cibo = context.user_data["cibo"]

    context.user_data.setdefault("lista_cibi", []).append((categoria, cibo, stack))

    testo = "📋 *Cibi selezionati:*\n\n"
    for cat, cb, st in context.user_data["lista_cibi"]:
        testo += f"- {st} stack di {cat} {cb}\n"

    keyboard = [
        [InlineKeyboardButton("➕ Aggiungi altro cibo", callback_data="continua")],
        [InlineKeyboardButton("✅ Conferma lista", callback_data="conferma")],
        [InlineKeyboardButton("🔄 Reset lista", callback_data="reset")],
    ]

    await update.message.reply_text(
        testo,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return CONFERMA


async def reset_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    return await start(query, context)


async def continua_scelta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await start(query, context)


async def conferma_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    testo = "🧾 *Ingredienti totali:*\n\n"
    ingredienti_totali = defaultdict(float)

    for cat, cibo, stack in context.user_data["lista_cibi"]:
        dati = MENU[cat][cibo]
        moltiplicatore = (stack * STACK_SIZE) / dati["output"]

        for nome, qta in dati["ingredienti"].items():
            if nome == "Salsa tartara":
                ingredienti_totali["Cetrioli"] += 1 * moltiplicatore
                ingredienti_totali["Cipolla"] += 1 * moltiplicatore
                ingredienti_totali["Maionese"] += 1 * moltiplicatore
            else:
                ingredienti_totali[nome] += qta * moltiplicatore

    for nome, qta in ingredienti_totali.items():
        testo += f"- {nome}: {format_stack(math.ceil(qta))}\n"

    await query.edit_message_text(testo, parse_mode="Markdown")
    await query.message.reply_text("Nome del dipendente incaricato?")
    return NOME_DIP


async def nome_dipendente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dipendente"] = update.message.text
    await update.message.reply_text("Nome di chi assegna l'incarico?")
    return NOME_CAPO


async def nome_capo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    capo = update.message.text
    dip = context.user_data["dipendente"]

    ruoli = {
        "blackshade15": "Direttrice",
        "andrygamer06": "Vice Dir.",
        "mrsh0t_": "Capocuoco",
    }

    ruolo = ruoli.get(capo.lower())

    if not ruolo:
        await update.message.reply_text("Non hai i permessi necessari!")
        context.user_data.clear()
        return ConversationHandler.END

    oggi = datetime.now()
    data_str = oggi.strftime("%d/%m/%Y")
    giorno = oggi.strftime("%a")

    testo = f"""📖 *Incarico*

{giorno} {data_str}
--------------------------------
-Preparare:
"""

    for cat, cb, st in context.user_data["lista_cibi"]:
        testo += f"- {st} stack di {cat} {cb}\n"

    testo += f"""

Al completamento dell'incarico assegnato è richiesta la controfirma di questo libro.

-Dipendente incaricato: {dip}

-Firma {ruolo}: {capo}
"""

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
            ],
            CIBO: [
                CallbackQueryHandler(scelta_cibo, pattern="^cibo\\|"),
                CallbackQueryHandler(reset_lista, pattern="^reset$"),
            ],
            STACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_stack)],
            CONFERMA: [
                CallbackQueryHandler(continua_scelta, pattern="^continua$"),
                CallbackQueryHandler(conferma_lista, pattern="^conferma$"),
                CallbackQueryHandler(reset_lista, pattern="^reset$"),
            ],
            NOME_DIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, nome_dipendente)],
            NOME_CAPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, nome_capo)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)

    PORT = int(os.environ.get("PORT", 10000))
    WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")

    app.run_webhook(listen="0.0.0.0", port=PORT, webhook_url=WEBHOOK_URL)


if __name__ == "__main__":
    main()
