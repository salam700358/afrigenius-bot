import logging
import os
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib import colors
import io

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Corriger un exercice", callback_data="exercice")],
        [InlineKeyboardButton("📄 Télécharger en PDF", callback_data="pdf")],
        [InlineKeyboardButton("ℹ️ À propos", callback_data="about")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌍 Bienvenue sur AfriGenius Bot!\n\n"
        "Je suis ton assistant IA pour corriger tes exercices de physique et mathématiques.\n\n"
        "Envoie-moi un exercice et je te donne la correction complète étape par étape !",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("⏳ Je résous ton exercice, patiente...")
    prompt = f"""Tu es un professeur expert en physique et mathématiques pour lycéens africains.
Corrige cet exercice étape par étape, de façon claire et pédagogique en français:

{user_text}

Donne: 1) Analyse du problème 2) Solution détaillée 3) Résultat final"""
    try:
        response = model.generate_content(prompt)
        correction = response.text
        context.user_data["last_correction"] = correction
        context.user_data["last_question"] = user_text
        keyboard = [[InlineKeyboardButton("📄 Télécharger en PDF", callback_data="pdf")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"✅ Correction:\n\n{correction}", reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text("❌ Erreur. Réessaie.")

  async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "pdf":
        correction = context.user_data.get("last_correction", "")
        question = context.user_data.get("last_question", "")
        if not correction:
            await query.message.reply_text("❌ Aucune correction disponible. Envoie d'abord un exercice.")
            return
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('title', parent=styles['Title'], textColor=colors.HexColor('#1a5276'), fontSize=16)
        body_style = ParagraphStyle('body', parent=styles['Normal'], fontSize=11, leading=16)
        content = []
        content.append(Paragraph("AfriGenius - Correction", title_style))
        content.append(Spacer(1, 0.5*cm))
        content.append(Paragraph(f"<b>Exercice:</b> {question}", body_style))
        content.append(Spacer(1, 0.3*cm))
        for line in correction.split('\n'):
            if line.strip():
                content.append(Paragraph(line, body_style))
                content.append(Spacer(1, 0.2*cm))
        doc.build(content)
        buffer.seek(0)
        await query.message.reply_document(document=buffer, filename="correction_afrigenius.pdf")
    elif query.data == "about":
        await query.message.reply_text("🌍 AfriGenius Bot\nCréé pour aider les élèves africains.\nPowered by Google Gemini AI.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
