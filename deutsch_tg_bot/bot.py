from pydoc import describe

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

from deutsch_tg_bot.command_handlers.training import select_training_type, training_handler
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DeutschLevel

training_router = Router()


class Training(StatesGroup):
    select_level = State()
    select_training_type = State()

    # For situation training
    describe_situation = State()
    situation_training_session = State()

    # For translation training
    add_sentence_constraint = State()
    translation_training_session = State()


@training_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Training.select_level)
    await message.answer(
        "Привіт! Я твій бот для вивчення німецької мови. Будь ласка, обери свій поточний рівень німецької:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=level.value) for level in settings.DEUTSCH_LEVELS]],
            resize_keyboard=True,
        ),
    )


@training_router.message(Training.select_level)
async def store_deutsch_level(message: Message, state: FSMContext) -> None:
    try:
        deutsch_level = DeutschLevel(message.text)
    except ValueError:
        await message.answer(
            "Обрано невірний рівень. Будь ласка, обери правильний рівень німецької з клавіатури."
        )
        return

    await state.update_data(deutsch_level=deutsch_level)
    await state.set_state(Training.select_training_type)

    await message.answer(
        f"Чудово! Ти обрав рівень {deutsch_level.value}",
        reply_markup=ReplyKeyboardRemove(),
    )

    select_training_type_keyboard = InlineKeyboardBuilder()
    select_training_type_keyboard.button(
        text="Рольова гра (ситуації)",
        callback_data="situation",
    )
    select_training_type_keyboard.button(
        text="Переклад речень",
        callback_data="translation",
    )
    await message.answer(
        "Тепер обери тип тренування:",
        reply_markup=select_training_type_keyboard.as_markup(),
    )


# Situation training handlers
@training_router.message(Training.select_training_type)
@training_router.callback_query(F.data == "situation")
async def select_training_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer("Ти обрав тренування 'Рольова гра (ситуації)'")
    await state.set_state(Training.describe_situation)
    await callback_query.message.answer(
        "Опиши ситуацію, в якій ти хочеш потренуватися (наприклад, 'Уяви, що ти в кафе і хочеш замовити каву')",
        reply_markup=ReplyKeyboardRemove(),
    )


@training_router.message(Training.describe_situation)
async def describe_situation(message: Message, state: FSMContext) -> None:
    await state.update_data(situation_description=message.text)
    await state.set_state(Training.situation_training_session)
    await message.answer("Ти в темній комнаті. Твої дії?")


@training_router.message(Training.situation_training_session)
async def situation_training_session(message: Message, state: FSMContext) -> None:
    await message.answer(
        f"Твоя відповідь: {message.text}\n\n(Тут буде відповідь від AI на основі опису ситуації та твоєї відповіді)"
    )


# Translation training handlers
@training_router.message(Training.select_training_type)
@training_router.callback_query(F.data == "translation")
async def select_training_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer("Ти обрав тренування 'Переклад речень'")
    await state.set_state(Training.add_sentence_constraint)
    await callback_query.message.answer(
        "Чи хочеш ти додати додаткові правила для генерації речень? "
        "(наприклад, 'Речення має містити слово immer')\n\n"
        "Якщо так, введи правила. Якщо ні, просто введи /skip.",
        reply_markup=ReplyKeyboardRemove(),
    )


@training_router.message(Training.add_sentence_constraint)
async def add_sentence_constraint(message: Message, state: FSMContext) -> None:
    if message.text and message.text != "/skip":
        await state.update_data(sentence_constraint=message.text)
        await message.answer(f"Правила збережено: {message.text}")

    await message.answer("1. Речення для перекладу")


async def start_bot() -> None:
    ic(settings.USERNAME_WHITELIST)
    tg_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(training_router)
    await dispatcher.start_polling(tg_bot)
