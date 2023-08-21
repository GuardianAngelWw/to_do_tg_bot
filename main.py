
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message,CallbackQuery
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram import executor
from markup import mainMenu
import database
from database import add_task_to_db, list_tasks_in_db, delete_task_from_db, update_task_status_in_db, checker, checker_done
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
import os


load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

async def on_startup(_):
    await database.db_start()
    print('bot started good')



@dp.message_handler(commands=['start'])
async def cmd_start(message: Message):
    welcome_message = f'Hello, {message.from_user.first_name}! I\'m a To-Do bot. Here are the available commands:'
    await message.answer(welcome_message, reply_markup=mainMenu)


@dp.callback_query_handler(lambda query: query.data == 'add')
async def cmd_add_task(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Enter a new task:")
    await dp.current_state(user=callback_query.from_user.id).set_state('add_task')


@dp.message_handler(state='add_task')
async def add_task(message: Message):
    task_text = message.text
    add_task_to_db(task_text)
    await message.answer(f"The task '{task_text}' has been added to the list.")
    await dp.current_state(user=message.from_user.id).reset_state()


@dp.callback_query_handler(lambda query: query.data == 'list')
async def list_tasks_callback(callback_query: CallbackQuery):
    tasks = list_tasks_in_db()
    if tasks:
        task_list_message = "Task list:\n"
        for task_id, task_name, task_status in tasks:
            status_symbol = "+" if task_status == 1 else "-"
            task_list_message += f"{task_id}. {status_symbol} {task_name}\n"
    else:
        task_list_message = "The list is empty."

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, task_list_message)


@dp.callback_query_handler(lambda query: query.data == 'done')
async def cmd_mark_done(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Enter the number of the task to mark as completed:")
    await dp.current_state(user=callback_query.from_user.id).set_state('mark_done')


@dp.message_handler(regexp=r'^\d+$', state="mark_done")
async def mark_done(message: types.Message):
    task_id = int(message.text)

    try:
        task_id = int(task_id)
        db_task = checker()
        a = False

        for mass in db_task:
            if mass == task_id:
                a = True
                break
        if a:
            if checker_done(task_id)[0] > 0:
                await message.answer(f"The task with the number {task_id} has already been marked!")
            else:
                update_task_status_in_db(task_id, 1)
                await message.answer(f"The task with the number {task_id} is marked as completed.")
        else:
            await message.answer(f"The task with the number {task_id} does not exist.")
    except ValueError:
        await message.answer("Error: Enter the correct task number (integer).")
    await dp.current_state(user=message.from_user.id).reset_state()


@dp.callback_query_handler(lambda query: query.data == 'delete')
async def cmd_delete_task(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Enter the number of the task you want to delete:")
    await dp.current_state(user=callback_query.from_user.id).set_state('delete')


@dp.message_handler(regexp=r'^\d+$', state="delete")
async def delete_task(message: types.Message):
    task_id = message.text

    try:
        task_id = int(task_id)
        db_task = checker()
        a = False

        for mass in db_task:
            if mass == task_id:
                a = True
                break

        if a:
            delete_task_from_db(task_id)
            await message.answer(f"The task with the number {task_id} has been deleted!")
        else:
            await message.answer("A task with this number was not found.")
    except ValueError:
        await message.answer("Error: Enter the correct task number (integer).")
    await dp.current_state(user=message.from_user.id).reset_state()





if __name__ == '__main__':
    executor.start_polling(dp,  on_startup=on_startup, skip_updates=True)
