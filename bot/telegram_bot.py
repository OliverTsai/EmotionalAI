from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN
from ai.ollama_client import ask_llm
from utils.logger import setup_logger


logger = setup_logger("telegram_bot")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start 指令。
    """

    user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    logger.info(f"/start from user_id={user_id}")

    await update.message.reply_text(
        "你好，我來陪你聊天❤️\n\n"
        "你可以直接跟我說今天發生了什麼，或告訴我你希望我記住的事情。"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help 指令。
    """

    user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    logger.info(f"/help from user_id={user_id}")

    help_text = (
        "你可以這樣和我聊天：\n\n"
        "1. 一般聊天：\n"
        "我今天有點累，可以陪我聊聊嗎？\n\n"
        "2. 讓我記住你的偏好：\n"
        "我喜歡你用溫柔一點的方式陪我。\n\n"
        "3. 讓我記住稱呼：\n"
        "我叫阿福，以後可以叫我哥哥。\n\n"
        "4. 測試記憶：\n"
        "你記得我喜歡你怎麼陪我嗎？"
    )

    await update.message.reply_text(help_text)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    處理一般文字訊息。
    """

    if update.message is None:
        logger.warning("收到 update，但 update.message 是 None")
        return

    user_message = update.message.text

    if not user_message or not user_message.strip():
        logger.info("收到空白訊息")
        await update.message.reply_text("我在這裡，你可以慢慢說。")
        return

    user_message = user_message.strip()

    telegram_user_id = str(update.effective_user.id) if update.effective_user else "unknown"
    username = update.effective_user.username if update.effective_user else ""
    full_name = update.effective_user.full_name if update.effective_user else ""

    logger.info(
        f"收到訊息 | user_id={telegram_user_id} | username={username} | "
        f"name={full_name} | message={user_message[:300]}"
    )

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        reply = ask_llm(user_message, user_id=telegram_user_id)

        if not reply or not reply.strip():
            logger.warning(f"ask_llm 回傳空回覆 | user_id={telegram_user_id}")
            reply = "我剛剛有點不知道該怎麼回，但我還在這裡。你可以再跟我說一次嗎？"

        logger.info(
            f"回覆成功 | user_id={telegram_user_id} | reply={reply[:300]}"
        )

        await update.message.reply_text(reply)

    except Exception:
        logger.exception(
            f"處理訊息時發生錯誤 | user_id={telegram_user_id} | message={user_message[:300]}"
        )

        await update.message.reply_text(
            "抱歉，我剛剛處理訊息時出了一點問題。\n"
            "你可以再傳一次給我，我會再試著回應你。"
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram Bot 全域錯誤處理。
    """

    logger.exception(f"Telegram Bot 全域錯誤 | update={update} | error={context.error}")


def main():
    """
    啟動 Telegram Bot。
    """

    logger.info("Telegram Bot 準備啟動")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    app.add_error_handler(error_handler)

    logger.info("Telegram Bot 已啟動")
    print("Telegram Bot 已啟動")

    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Telegram Bot 已由使用者手動停止")
        print("Telegram Bot 已停止")
