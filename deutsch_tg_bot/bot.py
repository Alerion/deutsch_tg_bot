from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from icecream import ic

from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.situation_training.tg_router import router as situation_training_router
from deutsch_tg_bot.translation_training.tg_router import router as translation_training_router

training_router = Router()
training_router.include_router(situation_training_router)
training_router.include_router(translation_training_router)


class Setup(StatesGroup):
    select_level = State()
    select_training_type = State()


@training_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Setup.select_level)

    select_deutsch_level_keyboard = InlineKeyboardBuilder()
    for level in settings.DEUTSCH_LEVELS:
        select_deutsch_level_keyboard.button(
            text=level.name,
            callback_data=f"select_deutsch_level:{level.value}",
        )

    await message.answer("Привіт! Я твій бот для вивчення німецької мови.")
    await message.answer(
        "Будь ласка, обери свій поточний рівень німецької:",
        reply_markup=select_deutsch_level_keyboard.as_markup(),
    )


@situation_training_router.callback_query(
    Setup.select_level, F.data.startswith("select_deutsch_level:")
)
async def store_deutsch_level(callback_query: CallbackQuery, state: FSMContext) -> None:
    assert callback_query.data is not None
    try:
        deutsch_level = DeutschLevel(callback_query.data.split(":")[1])
    except ValueError:
        await callback_query.answer(
            "Обрано невірний рівень. Будь ласка, обери правильний рівень німецької з клавіатури."
        )
        return

    await state.update_data(deutsch_level=deutsch_level)
    await state.set_state(Setup.select_training_type)

    assert isinstance(callback_query.message, Message)
    await callback_query.message.edit_text(
        f"Чудово! Ти обрав рівень {deutsch_level.value}",
    )

    select_training_type_keyboard = InlineKeyboardBuilder()
    select_training_type_keyboard.button(
        text="Рольова гра (ситуації)",
        callback_data="select_training_type:situation",
    )
    select_training_type_keyboard.button(
        text="Переклад речень",
        callback_data="select_training_type:translation",
    )
    await callback_query.message.answer(
        "Тепер обери тип тренування:",
        reply_markup=select_training_type_keyboard.as_markup(),
    )


async def start_bot() -> None:
    ic(settings.USERNAME_WHITELIST)
    tg_bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(training_router)
    await dispatcher.start_polling(tg_bot)
