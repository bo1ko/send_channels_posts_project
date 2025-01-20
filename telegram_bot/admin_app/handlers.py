import admin_app.db_requests as rq
import validators

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from admin_app.middlewares import CheckAndAddUserMiddleware
from admin_app.filters import IsAdmin
from admin_app.keyboards import get_callback_btns

from modules.telethon_user_bot.user_bot import UserBot

# routers
router = Router()
router.message.middleware(CheckAndAddUserMiddleware())
router.message.filter(IsAdmin())

admin_panel_btns = get_callback_btns(
    btns={
        "Редагувати аккаунти 📝": "edit_accounts",
        "Редагувати канали 📺": "edit_channels",
        "Статус бота 🤖": "bot_status",
    },
    sizes=(1, 1),
)

edit_accounts_btns = get_callback_btns(
    btns={
        "Статус аккаунтів 👤": "accounts_status",
        "Добавити аккаунт ✔": "add_account",
        "Видалити аккаунт ❌": "delete_account",
        "Назад 🔙": "admin",
    },
    sizes=(1, 2, 1),
)

back_edit_account_btn = get_callback_btns(
    btns={
        "Назад 🔙": "edit_accounts",
    }
)

edit_channels_btns = get_callback_btns(
    btns={
        "Список каналів 📺": "channels_list",
        "Добавити канал ✔": "add_channel",
        "Видалити канал ❌": "delete_channels",
        "Назад 🔙": "admin",
    },
    sizes=(1, 2, 1),
)

back_edit_channel_btn = get_callback_btns(
    btns={
        "Назад 🔙": "edit_channels",
    }
)


class AddAccount(StatesGroup):
    phone_number: str = State()
    api_id: int = State()
    api_hash: str = State()
    code: str = State()


class AddChannel(StatesGroup):
    title: str = State()
    url: str = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Адмін панель 👑", reply_markup=admin_panel_btns)


@router.callback_query(F.data == "admin")
async def callback_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Адмін панель 👑", reply_markup=admin_panel_btns)


@router.callback_query(F.data == "edit_accounts")
async def callback_edit_accounts(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Редагування аккаунтів 📝", reply_markup=edit_accounts_btns
    )


async def edit_accounts(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Редагування аккаунтів 📝", reply_markup=edit_accounts_btns)


@router.callback_query(F.data == "add_account")
async def callback_add_account_first_step(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введіть номер телефону 📱", reply_markup=back_edit_account_btn
    )
    await state.set_state(AddAccount.phone_number)


async def add_account_first_step(message: Message, state: FSMContext):
    await message.answer(
        "Введіть номер телефону 📱", reply_markup=back_edit_account_btn
    )
    await state.set_state(AddAccount.phone_number)


@router.message(AddAccount.phone_number)
async def add_account_second_step(message: Message, state: FSMContext, repeat=False):
    if not repeat:
        await state.update_data(phone_number="".join(message.text.split(" ")))

    await message.answer("Введіть API ID")
    await state.set_state(AddAccount.api_id)


@router.message(AddAccount.api_id)
async def add_account_third_step(message: Message, state: FSMContext):
    await state.update_data(api_id=message.text)

    if not message.text.isdigit():
        await message.answer("API ID повинен бути числом. Введіть API ID знову 👇")
        await add_account_second_step(message, state, repeat=True)
        return

    await message.answer("Введіть API HASH")
    await state.set_state(AddAccount.api_hash)


@router.message(AddAccount.api_hash)
async def add_account_fourth_step(message: Message, state: FSMContext):
    await state.update_data(api_hash=message.text)

    data = await state.get_data()
    phone_number = data["phone_number"]
    api_id = int(data["api_id"])
    api_hash = data["api_hash"]

    print(phone_number, api_id, api_hash)

    user_bot = UserBot()
    client = await user_bot.auth_first_step(phone_number, api_id, api_hash)

    if client:
        await message.answer("Введіть код")
        await state.update_data(
            client=client, phone_number=phone_number, user_bot=user_bot
        )
        await state.set_state(AddAccount.code)
    else:
        await message.answer(
            "Помилка авторизації. Перевірте номер телефону та API ключи. Введіть номер телефону знову 👇"
        )
        await add_account_first_step(message, state)
        return


@router.message(AddAccount.code)
async def add_account_fifth_step(message: Message, state: FSMContext):
    data = await state.get_data()
    phone_number = data["phone_number"]
    client = data["client"]
    user_bot = data["user_bot"]

    print(message.text, phone_number)
    result = await user_bot.auth_second_step(message.text, phone_number, client)

    if result:
        await message.answer("Аккаунт додано")
    else:
        await message.answer("Помилка авторизації. Спробуйте знову 🔃")

    await edit_accounts(message, state)


@router.callback_query(F.data == "delete_account")
async def callback_delete_accounts(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    accounts = await rq.get_telegram_accounts()
    btns = {}

    for key, value in accounts.items():
        btns[f"{key}"] = f"delete_account_{value[0]}"

    btns["Назад"] = "edit_accounts"

    delete_accounts_btns = get_callback_btns(
        btns=btns,
        sizes=(1, 1),
    )

    await callback.message.edit_text(
        "Видалення аккаунтів 📝", reply_markup=delete_accounts_btns
    )


@router.callback_query(F.data.startswith("delete_account_"))
async def callback_delete_account(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    account_pk = callback.data.split("_")[1]
    is_deleted = await rq.delete_telegram_account(int(account_pk))
    accounts = await rq.get_telegram_accounts()
    btns = {}

    for key, value in accounts.items():
        btns[f"{key}"] = f"delete_account_{value[0]}"

    delete_accounts_btns = get_callback_btns(
        btns=btns,
        sizes=(1, 1),
    )

    if is_deleted:
        await callback.answer("Аккаунт видалено")
    else:
        await callback.answer("Помилка при видаленні аккаунту")

    await callback.message.edit_text(
        "Видалення аккаунтів 📝", reply_markup=delete_accounts_btns
    )


@router.callback_query(F.data == "accounts_status")
async def callback_accounts_status(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    accounts = await rq.get_telegram_accounts()
    text = "Статус аккаунтів 📝\n\n"

    for key, value in accounts.items():
        text += f"👉 {key} - {'Активний' if value[1] else 'Неактивний'}\n"

    await callback.message.edit_text(text, reply_markup=back_edit_account_btn)


@router.callback_query(F.data == "edit_channels")
async def callback_edit_channels(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Редагування каналів 📝", reply_markup=edit_channels_btns
    )


async def edit_channels(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Редагування каналів 📝", reply_markup=edit_channels_btns)


@router.callback_query(F.data == "channels_list")
async def callback_channels_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    channels = await rq.get_telegram_channels()
    text = "Список каналів 📝\n\n"

    for key, value in channels.items():
        text += f"👉 {key} - {value[0]}\n{value[1]}\n\n"

    await callback.message.edit_text(text, reply_markup=back_edit_channel_btn)


@router.callback_query(F.data == "add_channel")
async def callback_add_channel_first_step(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Введіть назву каналу", reply_markup=back_edit_channel_btn
    )
    await state.set_state(AddChannel.title)


@router.message(AddChannel.title)
async def add_channel_second_step(message: Message, state: FSMContext, repeat=False):
    if not repeat:
        await state.update_data(title=message.text)
    await message.answer("Введіть URL каналу", reply_markup=back_edit_channel_btn)
    await state.set_state(AddChannel.url)


@router.message(AddChannel.url)
async def add_channel_third_step(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title")
    url = message.text

    if validators.url(url) is False:
        await message.answer(
            "Невалідний URL. Введіть url знову 🔃", reply_markup=back_edit_channel_btn
        )
        await add_channel_second_step(message, state, repeat=True)
        return

    account = await rq.get_min_telegram_channel()
    if not account:
        await message.answer(
            "Добавте спочатку аккаунт, щоб додати канал",
            reply_markup=back_edit_channel_btn,
        )
        return

    channel, created = await rq.get_or_create_telegram_channel(title, url, account)
    
    if not created:
        await message.answer("Канал вже існує", reply_markup=edit_channels_btns)
    user_bot = UserBot()
    result = await user_bot.join_channel(
        url, account.phone_number, account.api_id, account.api_hash
    )

    try:
        if result[1] == "in_channel":
            await message.answer("Користувач вже є у каналі", reply_markup=back_edit_channel_btn)
            return
    except Exception:
        pass

    if result:
        await message.answer("Канал додано", reply_markup=back_edit_channel_btn)
    else:
        await message.answer("Помилка при додаванні каналу. Спробуйте знову 🔃")
        await edit_channels(message, state)


@router.callback_query(F.data == "delete_channels")
async def callback_delete_channels(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    channels = await rq.get_telegram_channels()
    btns = {}

    for key, value in channels.items():
        btns[f"{value[0]}"] = f"delete_channel_{key}"

    if btns:
        btns["Назад"] = "edit_channels"

        await callback.message.edit_text(
            "Видалення каналів 📝",
            reply_markup=get_callback_btns(
                btns=btns,
                sizes=(1, 1),
            ),
        )
    else:
        await callback.message.edit_text(
            "Видалення каналів 📝", reply_markup=edit_channels_btns
        )


@router.callback_query(F.data.startswith("delete_channel_"))
async def callback_delete_channel(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    channel_pk = callback.data.split("_")[-1]
    is_deleted = await rq.delete_telegram_channel(int(channel_pk))
    channels = await rq.get_telegram_channels()
    btns = {}

    for key, value in channels.items():
        btns[f"{value[0]}"] = f"delete_channel_{key}"

    delete_channels_btns = get_callback_btns(
        btns=btns,
        sizes=(1, 1),
    )

    if is_deleted:
        await callback.answer("Канал видалено")
    else:
        await callback.answer("Помилка при видаленні каналу")

    if btns:
        btns["Назад"] = "edit_channels"

        await callback.message.edit_text(
            "Видалення каналів 📝", reply_markup=delete_channels_btns
        )
    else:
        await callback.message.edit_text(
            "Видалення каналів 📝", reply_markup=back_edit_channel_btn
        )
