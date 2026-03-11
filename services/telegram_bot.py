"""
services/telegram_bot.py
Telegram бот: команди керування + статус
"""

import asyncio, logging
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT, PUMP_MAX_SEC
from core.actuators import pump_on, pump_off, uv_on, uv_off
from services.database import insert_event

log = logging.getLogger("telegram")


async def send_message(text: str):
    """Надіслати повідомлення в чат."""
    try:
        from telegram import Bot
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT, text=text, parse_mode="Markdown")
    except Exception as e:
        log.error(f"send_message: {e}")


def _status_text(state: dict) -> str:
    p = "💧 ON" if state["pump"] else "⏹ OFF"
    v = "💜 ON" if state["uv"]   else "⏹ OFF"
    return (
        f"🌱 *SmartGrow Mini — Статус*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🌍 Ґрунт 1:  *{state['soil1']}%*\n"
        f"🌍 Ґрунт 2:  *{state['soil2']}%*\n"
        f"🌡 Темп:     *{state['temp']}°C*\n"
        f"💦 Повітря:  *{state['hum_air']}%*\n"
        f"⚡ Батарея:  *{state.get('battery', '?')}%*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🚿 Насос:    {p}\n"
        f"💜 UV LED:   {v}\n"
        f"⏰ Полив:    {state['last_water']}\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )


def run_bot(state: dict):
    """Запустити бота в окремому event loop (викликати в потоці)."""
    if TELEGRAM_TOKEN == "ВСТАВТЕ_ТОКЕН_ТУТ":
        log.warning("Telegram токен не вставлено — бот вимкнено")
        return

    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, ContextTypes

        async def cmd_status(u: Update, c: ContextTypes.DEFAULT_TYPE):
            await u.message.reply_text(_status_text(state), parse_mode="Markdown")

        async def cmd_water(u: Update, c: ContextTypes.DEFAULT_TYPE):
            if state["pump"]:
                await u.message.reply_text("⚠️ Насос вже працює!"); return
            pump_on()
            state["pump"] = True
            state["last_water"] = datetime.now().strftime("%H:%M")
            insert_event("PUMP_MANUAL", "Полив запущено вручну через Telegram")
            await u.message.reply_text(f"🚿 Полив запущено на {PUMP_MAX_SEC}с...")
            await asyncio.sleep(PUMP_MAX_SEC)
            pump_off()
            state["pump"] = False
            await u.message.reply_text("✅ Полив завершено!")

        async def cmd_uv_on(u: Update, c: ContextTypes.DEFAULT_TYPE):
            uv_on(); state["uv"] = True
            insert_event("UV_MANUAL_ON", "UV увімкнено вручну")
            await u.message.reply_text("💜 UV LED увімкнено!")

        async def cmd_uv_off(u: Update, c: ContextTypes.DEFAULT_TYPE):
            uv_off(); state["uv"] = False
            insert_event("UV_MANUAL_OFF", "UV вимкнено вручну")
            await u.message.reply_text("⏹ UV LED вимкнено!")

        async def cmd_help(u: Update, c: ContextTypes.DEFAULT_TYPE):
            await u.message.reply_text(
                "🌱 *SmartGrow Mini — Команди*\n\n"
                "/status — стан системи\n"
                "/water  — полив вручну\n"
                "/uvon   — UV увімкнути\n"
                "/uvoff  — UV вимкнути\n"
                "/help   — ця довідка",
                parse_mode="Markdown"
            )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        for cmd, fn in [
            ("status", cmd_status), ("water", cmd_water),
            ("uvon",   cmd_uv_on),  ("uvoff", cmd_uv_off),
            ("help",   cmd_help),
        ]:
            app.add_handler(CommandHandler(cmd, fn))

        log.info("🤖 Telegram бот запущено")
        app.run_polling(stop_signals=None)

    except Exception as e:
        log.error(f"run_bot: {e}")
