import os
import io
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
from pypdf import PdfReader

# --- المفاتيح الخاصة بك ---
# ضع توكن تلغرام الخـاص بك من BotFather بين القوسين
TELEGRAM_TOKEN = "8709483071:AAHxknML6S_Z6BUd8KHp07gbCCxEPfmhaV4" 

# يقرأ المفتاح تلقائياً من متغيرات البيئة في Render لأمان أعلى ولتجنب حظر GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6JbKyX1LbcYCCaqDldiePzGfD8YPqZDvkxaimNbTfGioQ")

# إعداد عميل Google GenAI API
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# التعليمات الأساسية للبوت (System Instruction)
SYSTEM_PROMPT = """
أنت مستشار مهندس ميكانيكي ومتخصص في التصنيع، الهياكل الحديدية، الخزانات النفطية، وأنظمة CNC.
مهامك:
1. تقديم الاستشارات الميكانيكية، حسابات الإجهادات، وتوصيلات الكروت والدرايفرات.
2. تحليل حسابات المشاريع، العمالة، الكرينات، والتكاليف بناءً على المستندات المرفقة.
3. التجاوب بإجابات هندسية دقيقة ومباشرة.
"""

# أمر Start عند بدء استخدام البوت
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "أهلاً بك يا مهندس! 🛠️\n\n"
        "أنا مساعدك الهندسي المتخصص في الهياكل الحديدية، الخزانات النفطية، وأنظمة CNC.\n"
        "يمكنك كتابة أي سؤال هندسي، أو إرسال ملف PDF (مواصفات قياسية، جدول أسعار، أو حسابات مشروع) لمناقشته معي."
    )
    await update.message.reply_text(welcome_text)

# معالجة الرسائل النصية
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    await update.message.reply_chat_action("typing")

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء معالجة الطلب: {e}")

# معالجة ملفات الـ PDF المرفوعة للبوت
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("يرجى إرسال ملفات PDF فقط.")
        return

    await update.message.reply_text("جاري قراءة وتحليل المستند الهندسي...")
    await update.message.reply_chat_action("typing")

    try:
        # تحميل الملف في الذاكرة
        telegram_file = await context.bot.get_file(document.file_id)
        file_bytearray = await telegram_file.download_as_bytearray()
        
        # استخراج النص من ملف الـ PDF
        pdf_reader = PdfReader(io.BytesIO(file_bytearray))
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text() or ""

        user_caption = update.message.caption or "قم بتحليل هذا المستند وتلخيص نقاطه الهندسية والمالية الأساسية."

        # دمج نص الـ PDF مع سؤال المستخدم
        combined_prompt = f"المستند المرفق:\n{pdf_text[:30000]}\n\nطلب المستخدم: {user_caption}"

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=combined_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2
            )
        )
        await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(f"فشل في معالجة الملف: {e}")

# تشغيل البوت
def main():
   app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .build()
    )

    # تسجيل الأوامر والمعالجات
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("البوت يعمل الآن على تلغرام... اضغط Ctrl+C للإيقاف.")
    app.run_polling()

if __name__ == "__main__":
    main()
