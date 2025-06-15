import os
import paramiko
import tempfile
from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)


ASK_TYPE, RECEIVE_KEY, ASK_PASSWORD, ASK_COMMAND = range(4)


TELEGRAM_TOKEN = "API_KEY"
AUTHORIZED_USERS = {123456789}
user_auth: dict[int, dict] = {}


async def error_and_restart(update: Update, context: ContextTypes.DEFAULT_TYPE, msg):
    if msg != None:
        await update.message.reply_text(f"Помилка: {msg}")

    await update.message.reply_text("Для початку знову введіть:\n/ssh_connect <host> <user>")

    return ConversationHandler.END

def cleanup_user_data(user_id: int):
    info = user_auth.pop(user_id, None)
    if info and info["auth_type"] == "key":
        try:
            os.remove(info["auth_data"])

        except Exception:
            ...

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я — SSH Bot.\n"
        "Щоб почати, введіть:\n"
        "``` /ssh_connect <host> <user>```",
        parse_mode="Markdown"
    )

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Запуститb бота"),
        BotCommand("ssh_connect", "Почати SSH‑сессию"),
        BotCommand("ssh_disconnect", "Відключитися от сессии")
    ])

async def ssh_connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        return await error_and_restart(update, context, "Неправильний формат")

    host, ssh_user = args
    context.user_data.update({"host": host, "ssh_user": ssh_user})

    await update.message.reply_text(
        "Оберіть метод авторизації:",
        reply_markup=ReplyKeyboardMarkup([["🔑 key"], ["🔒 password"]], one_time_keyboard=True)
    )

    return ASK_TYPE

async def ask_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "key" in text:
        await update.message.reply_text(
            "🔑 Надішліть файл вашого приватного SSH ключа",
            parse_mode="Markdown"
        )

        return RECEIVE_KEY

    elif "password" in text:
        await update.message.reply_text(
            "🔒 Введіть ваш пароль у вигляді тексту",
            parse_mode="Markdown"
        )

        return ASK_PASSWORD

    else:
        return await error_and_restart(update, context, "Оберіть 'key' або 'password'")

async def receive_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc:
        return await error_and_restart(update, context, "Очікується файл ключа")

    file = await doc.get_file()
    suffix = os.path.splitext(doc.file_name)[1] or ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    await file.download_to_drive(tmp.name)

    user_auth[update.effective_user.id] = {
        "auth_type": "key",
        "auth_data": tmp.name,
        "client": None
    }

    await update.message.reply_text("Файл ключа отримано.\nТепер введіть команду для виконання:")

    return ASK_COMMAND

async def ask_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pwd = update.message.text
    user = update.effective_user
    user_auth[user.id] = {"auth_type": "password", "auth_data": pwd}
    await update.message.reply_text("Пароль отримано! Тепер введіть команду")

    return ASK_COMMAND

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    info = user_auth.get(user.id)
    cmd = update.message.text.strip()

    if cmd.lower() in ("/exit", "/ssh_disconnect"):
        cleanup_user_data(user.id)
        await update.message.reply_text("🔌 SSH-сеанс успішно завершено")

        return ConversationHandler.END

    host = context.user_data["host"]
    ssh_user = context.user_data["ssh_user"]
    client = info.get("client")

    if client is None:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if info["auth_type"] == "key":
            client.connect(hostname=host, username=ssh_user, key_filename=info["auth_data"])

        else:
            client.connect(hostname=host, username=ssh_user, password=info["auth_data"])

        info["client"] = client

    prompt = f"{ssh_user}@{host}:$ "

    await update.message.reply_text(f"Виконую `{cmd}`...", parse_mode="Markdown")

    try:
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode() + stderr.read().decode()

    except Exception as e:
        out = f"Error: {e}"

    if len(out) > 4000:
        out = out[:4000] + "\n...[truncated]"

    await update.message.reply_text(f"<pre>{prompt}{cmd}\n{out}</pre>", parse_mode="HTML")

    return ASK_COMMAND


async def ssh_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cleanup_user_data(update.effective_user.id)
    await update.message.reply_text("🔌 SSH‑сессія завершена")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cleanup_user_data(update.effective_user.id)
    await update.message.reply_text("Скасовано")

    return ConversationHandler.END


def main():
    app = ApplicationBuilder() \
        .token(TELEGRAM_TOKEN) \
        .post_init(post_init) \
        .build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("ssh_connect", ssh_connect)],
        states={
            ASK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_type)],
            RECEIVE_KEY: [MessageHandler(filters.Document.ALL, receive_key)],
            ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_password)],
            ASK_COMMAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_command)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("ssh_disconnect", ssh_disconnect)]
    )


    app.add_handler(conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ssh_disconnect", ssh_disconnect))
    app.run_polling()


if __name__ == "__main__":
    main()
