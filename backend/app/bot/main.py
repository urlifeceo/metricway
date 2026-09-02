import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings
from app.core.clickhouse import get_ch_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkProjectSG(StatesGroup):
    waiting_for_name = State()

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext):
    project_token = command.args

    if not project_token:
        await message.answer(
            "Чтобы привязать проект к этому чату, передай токен:\n"
            "<code>/start YOUR_PROJECT_TOKEN</code>",
            parse_mode="HTML"
        )
        return

    await state.update_data(project_token=project_token)
    await state.set_state(LinkProjectSG.waiting_for_name)
    await message.answer("Введите название для вашего проекта (например, <i>My Main Bot</i>):", parse_mode="HTML")

@dp.message(LinkProjectSG.waiting_for_name)
async def process_project_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    project_token = user_data["project_token"]
    project_name = message.text.strip()

    ch_client = get_ch_client()
    query = """
    INSERT INTO tgmetrics.projects (project_token, name, alert_chat_id, is_active, updated_at)
    VALUES ({project_token:String}, {name:String}, {chat_id:Int64}, 1, now())
    """
    
    try:
        ch_client.query(
            query,
            parameters={
                "project_token": project_token,
                "name": project_name,
                "chat_id": message.chat.id
            }
        )
        await message.answer(
            f"✅ Проект <b>{project_name}</b> успешно привязан!\n"
            f"Каждое утро в 09:00 сюда будет приходить сводка.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to link project in ClickHouse: {e}")
        await message.answer("❌ Ошибка при сохранении данных в ClickHouse.")
    
    await state.clear()

async def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing!")
        return
    logger.info("Starting Telegram Bot worker...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())