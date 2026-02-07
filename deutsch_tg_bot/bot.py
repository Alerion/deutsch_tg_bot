from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from icecream import ic
from rich import print as rprint

from deutsch_tg_bot import situation_training
from deutsch_tg_bot.command_handlers.training import select_training_type, training_handler
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.translation_training.tg_router import router

training_router = Router()
situation_training_router = Router()
training_router.include_router(situation_training_router)
training_router.include_router(router)


class Setup(StatesGroup):
    select_level = State()
    select_training_type = State()


class SituationTraining(StatesGroup):
    describe_situation = State()
    situation_training_session = State()


@training_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Setup.select_level)
    await message.answer(
        "Привіт! Я твій бот для вивчення німецької мови. Будь ласка, обери свій поточний рівень німецької:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=level.value) for level in settings.DEUTSCH_LEVELS]],
            resize_keyboard=True,
        ),
    )


@training_router.message(Setup.select_level)
async def store_deutsch_level(message: Message, state: FSMContext) -> None:
    try:
        deutsch_level = DeutschLevel(message.text)
    except ValueError:
        await message.answer(
            "Обрано невірний рівень. Будь ласка, обери правильний рівень німецької з клавіатури."
        )
        return

    await state.update_data(deutsch_level=deutsch_level)
    await state.set_state(Setup.select_training_type)

    await message.answer(
        f"Чудово! Ти обрав рівень {deutsch_level.value}",
        reply_markup=ReplyKeyboardRemove(),
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
    await message.answer(
        "Тепер обери тип тренування:",
        reply_markup=select_training_type_keyboard.as_markup(),
    )


# Situation training handlers
@situation_training_router.callback_query(F.data == "select_training_type:situation")
async def select_training_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer("Ти обрав тренування 'Рольова гра (ситуації)'")
    await state.set_state(SituationTraining.describe_situation)
    await callback_query.message.answer(
        "Опиши ситуацію, в якій ти хочеш потренуватися (наприклад, 'Уяви, що ти в кафе і хочеш замовити каву')",
        reply_markup=ReplyKeyboardRemove(),
    )


@situation_training_router.message(SituationTraining.describe_situation)
async def describe_situation(message: Message, state: FSMContext) -> None:
    await state.update_data(situation_description=message.text)
    await state.set_state(SituationTraining.situation_training_session)
    await message.answer("Ти в темній комнаті. Твої дії?")


@situation_training_router.message(SituationTraining.situation_training_session)
async def situation_training_session(message: Message, state: FSMContext) -> None:
    await message.answer(
        f"Твоя відповідь: {message.text}\n\n(Тут буде відповідь від AI на основі опису ситуації та твоєї відповіді)"
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
