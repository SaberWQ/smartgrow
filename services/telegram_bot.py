# /home/smartgrow/services/telegram_bot.py
#
# Telegram бот з LangChain AI агентом.
# Агент має доступ до інструментів:
#   get_status   — поточний стан системи
#   water_now    — запустити полив
#   set_uv       — увімкнути/вимкнути UV
#   get_history  — дані за останню годину
#   get_events   — останні події
# Агент розуміє природну мову: "полий рослину", "як справи у теплиці?",
# "покажи графік вологості", "вимкни лампу" тощо.

import asyncio, logging, time
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT, PUMP_MAX_SEC, OPENAI_API_KEY

log = logging.getLogger("telegram")

# ── Глобальний state (встановлюється з main.py) ──────────────
_state = {}


def set_state(state: dict):
    global _state
    _state = state


# ── Надіслати повідомлення (викликається з alerts.py) ────────
async def send_message(text: str):
    try:
        from telegram import Bot
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT, text=text, parse_mode="Markdown")
    except Exception as e:
        log.error("send_message: %s", e)


# ════════════════════════════════════════════════════════════
#  LangChain інструменти (Tools)
# ════════════════════════════════════════════════════════════

def _tool_get_status(_input: str = "") -> str:
    """Повертає поточний стан теплиці."""
    s = _state
    if not s:
        return "State not available."
    return (
        "SmartGrow Mini Status:\n"
        "Soil 1:      %d%%\n"
        "Soil 2:      %d%%\n"
        "Temperature: %.1f C\n"
        "Air humidity:%.0f%%\n"
        "Battery:     %d%%\n"
        "Pump:        %s\n"
        "UV LED:      %s\n"
        "Last water:  %s\n"
        "Time:        %s"
    ) % (
        s.get("soil1", 0), s.get("soil2", 0),
        s.get("temp",  0), s.get("hum_air", 0),
        s.get("battery", 100),
        "ON" if s.get("pump") else "OFF",
        "ON" if s.get("uv")   else "OFF",
        s.get("last_water", "--"),
        datetime.now().strftime("%d.%m.%Y %H:%M"),
    )


def _tool_water_now(_input: str = "") -> str:
    """Запустити полив негайно."""
    from core.actuators import pump_on, pump_off
    from services.database import insert_event
    if _state.get("pump"):
        return "Pump is already running!"
    pump_on()
    _state["pump"]       = True
    _state["last_water"] = datetime.now().strftime("%H:%M")
    insert_event("PUMP_MANUAL", "Manual watering via AI agent")
    time.sleep(PUMP_MAX_SEC)
    pump_off()
    _state["pump"] = False
    return "Watering complete! Duration: %ds." % PUMP_MAX_SEC


def _tool_set_uv(on_off: str) -> str:
    """Увімкнути або вимкнути UV LED. Вхід: 'on' або 'off'."""
    from core.actuators import uv_on, uv_off
    from services.database import insert_event
    cmd = on_off.strip().lower()
    if cmd in ("on", "1", "true", "увімкни", "вкл", "включи"):
        uv_on()
        _state["uv"] = True
        insert_event("UV_ON", "UV turned on by AI agent")
        return "UV LED turned ON."
    else:
        uv_off()
        _state["uv"] = False
        insert_event("UV_OFF", "UV turned off by AI agent")
        return "UV LED turned OFF."


def _tool_get_history(_input: str = "") -> str:
    """Дані датчиків за останню годину (останні 10 записів)."""
    from services.database import get_history
    rows = get_history(minutes=60)
    if not rows:
        return "No data yet."
    rows = rows[-10:]
    lines = ["Time      | G1% | G2% | Temp | Hum"]
    lines.append("-" * 38)
    for r in rows:
        ts = str(r.get("timestamp", ""))[-8:-3]
        lines.append("%s | %3d | %3d | %4.1f | %3.0f" % (
            ts, r.get("soil1", 0), r.get("soil2", 0),
            r.get("temp", 0), r.get("hum_air", 0)))
    return "\n".join(lines)


def _tool_get_events(_input: str = "") -> str:
    """Останні 10 подій системи."""
    from services.database import get_events
    rows = get_events(limit=10)
    if not rows:
        return "No events yet."
    lines = []
    for r in rows:
        ts  = str(r.get("timestamp", ""))[-8:-3]
        typ = r.get("event_type", "")
        msg = r.get("message", "")
        lines.append("[%s] %s: %s" % (ts, typ, msg))
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
#  Побудова LangChain агента
# ════════════════════════════════════════════════════════════

def _build_agent():
    """Будує LangChain агента з інструментами і пам'яттю."""
    import os
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    from langchain_openai import ChatOpenAI
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.memory import ConversationBufferWindowMemory
    from langchain_core.tools import Tool
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    llm = ChatOpenAI(
        model=__import__("config").OPENAI_MODEL,
        temperature=0.3,
        max_tokens=512,
    )

    tools = [
        Tool(
            name="get_status",
            func=_tool_get_status,
            description=(
                "Get current greenhouse status: soil moisture, temperature, "
                "humidity, battery, pump and UV state. "
                "Use when user asks about current state, status, conditions."
            ),
        ),
        Tool(
            name="water_now",
            func=_tool_water_now,
            description=(
                "Start watering the plant immediately. "
                "Use when user asks to water, irrigate, or the plant needs water."
            ),
        ),
        Tool(
            name="set_uv",
            func=_tool_set_uv,
            description=(
                "Turn UV LED on or off. Input must be 'on' or 'off'. "
                "Use when user asks to turn on/off the lamp, UV, light."
            ),
        ),
        Tool(
            name="get_history",
            func=_tool_get_history,
            description=(
                "Get sensor readings from the last hour. "
                "Use for trends, graphs, historical data requests."
            ),
        ),
        Tool(
            name="get_events",
            func=_tool_get_events,
            description=(
                "Get recent system events (watering, UV changes, alerts). "
                "Use when user asks about recent activity or event log."
            ),
        ),
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are SmartGrow AI — an intelligent assistant for an autonomous "
         "mini greenhouse (SmartGrow Mini). You control soil moisture sensors, "
         "a water pump, UV LED grow light, temperature/humidity sensor, and a "
         "battery-powered Raspberry Pi system.\n\n"
         "Rules:\n"
         "- Always respond in the same language the user wrote in\n"
         "- Be concise and friendly\n"
         "- Use tools to get real data before answering status questions\n"
         "- For watering or UV control, confirm the action after using the tool\n"
         "- If soil moisture < 20%, proactively suggest watering\n"
         "- Format numbers neatly, use emojis sparingly"),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=8,  # зберігати останні 8 обмінів
    )

    agent = create_openai_functions_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=4,
    )
    return executor


# ════════════════════════════════════════════════════════════
#  Telegram хендлери
# ════════════════════════════════════════════════════════════

def run_bot(state: dict):
    set_state(state)

    if TELEGRAM_TOKEN == "ВСТАВТЕ_ТОКЕН_ТУТ":
        log.warning("Telegram token not set — bot disabled")
        return

    # Перевіряємо чи є OpenAI ключ
    use_ai = OPENAI_API_KEY != "ВСТАВТЕ_OPENAI_KEY_ТУТ"
    agent  = None

    if use_ai:
        try:
            agent = _build_agent()
            log.info("LangChain agent ready")
        except Exception as e:
            log.error("LangChain init failed: %s", e)
            use_ai = False

    try:
        from telegram import Update
        from telegram.ext import (Application, CommandHandler,
                                   MessageHandler, ContextTypes, filters)

        # ── /start ──────────────────────────────────────────
        async def cmd_start(u: Update, c: ContextTypes.DEFAULT_TYPE):
            ai_note = (
                "\n\nAI-агент *активний* — пишіть будь-що на звичайній мові!"
                if use_ai else
                "\n\n_AI-агент вимкнено (немає OPENAI_API_KEY)_"
            )
            await u.message.reply_text(
                "*SmartGrow Mini*\n"
                "Автономна мікротеплиця\n\n"
                "/status — стан системи\n"
                "/water  — полив вручну\n"
                "/uvon   — UV увімкнути\n"
                "/uvoff  — UV вимкнути\n"
                "/history — дані за годину\n"
                "/events  — останні події\n"
                "/help   — ця довідка"
                + ai_note,
                parse_mode="Markdown",
            )

        # ── /status ─────────────────────────────────────────
        async def cmd_status(u: Update, c: ContextTypes.DEFAULT_TYPE):
            txt = _tool_get_status()
            await u.message.reply_text("```\n%s\n```" % txt,
                                       parse_mode="Markdown")

        # ── /water ──────────────────────────────────────────
        async def cmd_water(u: Update, c: ContextTypes.DEFAULT_TYPE):
            if state.get("pump"):
                await u.message.reply_text("Насос вже працює!"); return
            await u.message.reply_text("Запускаю полив...")
            result = await asyncio.get_event_loop().run_in_executor(
                None, _tool_water_now, "")
            await u.message.reply_text(result)

        # ── /uvon /uvoff ─────────────────────────────────────
        async def cmd_uv_on(u: Update, c: ContextTypes.DEFAULT_TYPE):
            result = await asyncio.get_event_loop().run_in_executor(
                None, _tool_set_uv, "on")
            await u.message.reply_text(result)

        async def cmd_uv_off(u: Update, c: ContextTypes.DEFAULT_TYPE):
            result = await asyncio.get_event_loop().run_in_executor(
                None, _tool_set_uv, "off")
            await u.message.reply_text(result)

        # ── /history ─────────────────────────────────────────
        async def cmd_history(u: Update, c: ContextTypes.DEFAULT_TYPE):
            txt = _tool_get_history()
            await u.message.reply_text("```\n%s\n```" % txt,
                                       parse_mode="Markdown")

        # ── /events ──────────────────────────────────────────
        async def cmd_events(u: Update, c: ContextTypes.DEFAULT_TYPE):
            txt = _tool_get_events()
            await u.message.reply_text("```\n%s\n```" % txt,
                                       parse_mode="Markdown")

        # ── /help ────────────────────────────────────────────
        async def cmd_help(u: Update, c: ContextTypes.DEFAULT_TYPE):
            await cmd_start(u, c)

        # ── AI: будь-яке текстове повідомлення ──────────────
        async def handle_message(u: Update, c: ContextTypes.DEFAULT_TYPE):
            if not use_ai or agent is None:
                await u.message.reply_text(
                    "AI-агент вимкнено. Використовуй команди: "
                    "/status /water /uvon /uvoff /history /events")
                return

            user_text = u.message.text or ""
            await u.message.reply_chat_action("typing")

            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.invoke({"input": user_text})
                )
                answer = result.get("output", "No response.")
                await u.message.reply_text(answer)
            except Exception as e:
                log.error("Agent error: %s", e)
                await u.message.reply_text(
                    "Помилка AI агента. Спробуй команди: "
                    "/status /water /uvon /uvoff")

        # ── Збираємо Application ─────────────────────────────
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        app = Application.builder().token(TELEGRAM_TOKEN).build()

        app.add_handler(CommandHandler("start",   cmd_start))
        app.add_handler(CommandHandler("help",    cmd_help))
        app.add_handler(CommandHandler("status",  cmd_status))
        app.add_handler(CommandHandler("water",   cmd_water))
        app.add_handler(CommandHandler("uvon",    cmd_uv_on))
        app.add_handler(CommandHandler("uvoff",   cmd_uv_off))
        app.add_handler(CommandHandler("history", cmd_history))
        app.add_handler(CommandHandler("events",  cmd_events))
        # AI handler — тільки текстові повідомлення що не команди
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, handle_message))

        log.info("Telegram bot started (AI=%s)", use_ai)
        app.run_polling(stop_signals=None)

    except Exception as e:
        log.error("run_bot: %s", e)
