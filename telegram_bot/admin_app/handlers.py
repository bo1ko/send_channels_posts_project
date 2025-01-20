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
from apscheduler.schedulers.background import BackgroundScheduler

from modules.telethon_user_bot.user_bot import UserBot
from cron import start_cron

# routers
router = Router()
router.message.middleware(CheckAndAddUserMiddleware())
router.message.filter(IsAdmin())

admin_panel_btns = get_callback_btns(
    btns={
        "Редагувати аккаунти 📝": "edit_accounts",
        "Редагувати канали 📺": "edit_channels",
        "Редагувати час роботи 🕒": "change_time",
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

bot_status_inactive_btns = get_callback_btns(
    btns={
        "Запустити бота": "bot_start",
        "Назад": "admin",
    },
    sizes=(1,),
)

bot_status_active_btns = get_callback_btns(
    btns={
        "Зупинити бота": "bot_stop",
        "Назад": "admin",
    },
    sizes=(1,),
)

scheduler = BackgroundScheduler()
parsing_job = None
parsing_status = False


class AddAccount(StatesGroup):
    phone_number: str = State()
    api_id: int = State()
    api_hash: str = State()
    code: str = State()


class AddChannel(StatesGroup):
    title: str = State()
    url: str = State()

class ChangeTime(StatesGroup):
    wait_time: int = State()


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

    result = await user_bot.auth_second_step(message.text, phone_number, client)

    if result:
        await rq.add_telegram_account(phone_number, client.api_id, client.api_hash)
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


    user_bot = UserBot()
    result = await user_bot.join_channel(
        url, account.phone_number, account.api_id, account.api_hash
    )

    if result[1] == "in_channel":
        await message.answer(
            "Користувач вже є у каналі", reply_markup=back_edit_channel_btn
        )
        return
    elif result[1] == "free":
        channel, created = await rq.get_or_create_telegram_channel(title, url, account, channel_id=result[2])

        if not created:
            await message.answer("Канал вже існує", reply_markup=edit_channels_btns)
            return

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


@router.callback_query(F.data == "bot_status")
async def callback_bot_status(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if parsing_status:
        await callback.message.edit_text(
            "Статус бота: Активний", reply_markup=bot_status_active_btns
        )
    else:
        await callback.message.edit_text(
            "Статус бота: Неактивний", reply_markup=bot_status_inactive_btns
        )


@router.callback_query(F.data == "bot_start")
async def callback_bot_start(callback: CallbackQuery):
    global parsing_status, parsing_job

    if not parsing_status:
        telegram = await rq.get_telegram_accounts()

        if not telegram:
            await callback.answer(
                "Добавте спочатку аккаунт, щоб запустити бота",
                reply_markup=back_edit_channel_btn,
            )
            return
        
        wait_time = int(open("time.txt", "r").read())

        parsing_job = scheduler.add_job(
            start_cron,
            "interval",
            seconds=wait_time,
        )
        scheduler.start()
        parsing_status = True
        await callback.message.edit_text(
            "Статус бота: Активний", reply_markup=bot_status_active_btns
        )
        await callback.answer("Запускаю парсинг")
    else:
        await callback.answer("Парсинг вже активний!")


@router.callback_query(F.data == "bot_stop")
async def callback_bot_stop(callback: CallbackQuery):
    global parsing_status, parsing_job

    if parsing_status:
        if parsing_job:
            parsing_job.remove()
        parsing_status = False
        await callback.message.edit_text(
            "Статус бота: Неактивний", reply_markup=bot_status_inactive_btns
        )
        await callback.answer("Зупиняю парсинг")
    else:
        await callback.answer("Парсинг вже зупинено!")

@router.callback_query(F.data == "change_time")
async def callback_change_time_first(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    current_time = open("time.txt", "r").read()
    await callback.message.edit_text(
        f"Введіть час запуску парсингу, теперішній час: {current_time}", reply_markup=get_callback_btns(btns={"Назад": "admin"})
    )
    await state.set_state(ChangeTime.wait_time)

async def change_time_first(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Введіть час запуску парсингу", reply_markup=get_callback_btns(btns={"Назад": "admin"})
    )
    await state.set_state(ChangeTime.wait_time)


@router.message(ChangeTime.wait_time)
async def change_time_second(message: Message, state: FSMContext):
    if message.text.isdigit() and int(message.text) >= 60:
        with open("time.txt", "w") as f:
            f.write(message.text)
    else:
        await message.answer("Введіть число (мін: 60с.)")
        change_time_first(message, state)
        return

    await state.clear()
    await message.answer("Час змінено", reply_markup=get_callback_btns(btns={"Назад": "admin"}))
