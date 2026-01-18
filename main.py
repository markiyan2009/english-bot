from db import *
# Bot token can be obtained via https://t.me/BotFather
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
TOKEN_API = os.getenv("TOKEN_API")
@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:

    kb = [[ types.KeyboardButton(text="Записати слово"), types.KeyboardButton(text="Згенерувати тест")],]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="бойко")
    await message.answer("Виберіть дію", reply_markup=keyboard)


@dp.message(F.text == 'Записати слово')
async def get_word_state(message: types.Message, state: FSMContext) -> None:
    try:
        await message.answer('Напишіть слово')
        await state.set_state(WordState.waiting_word)
        
    except TypeError:
        await message.answer("Nice try!")

@dp.message(WordState.waiting_word)
async def get_word(message: types.Message, state: FSMContext):
    word = message.text
    # запис у базу...
    word_id = add_word_data(word)
    await state.update_data(word_id=word_id)
    await message.answer(f"Слово '{word}' записано!")
    
    await message.answer('Запишіть переклад')
    await state.set_state(WordState.waiting_translation)

@dp.message(WordState.waiting_translation)
async def get_translation(message: types.Message, state: FSMContext):
    translation = message.text
    # запис у базу...
    data = await state.get_data()
    word_id = int(data.get("word_id"))
    await state.update_data(trans=translation)
    await message.answer("Переклад записано")
    await state.set_state(WordState.waiting_explenation)
    await message.answer("Запишіть пояснення(якщо його немає запишіть 0)")

@dp.message(WordState.waiting_explenation)
async def get_explenation(message: types.Message,state:FSMContext):
    explenation = message.text
    data = await state.get_data()
    word_id = int(data.get("word_id"))
    trans = str(data.get("trans"))
    if explenation == "0":

        add_trans_data(trans,word_id,None)
    else:
        add_trans_data(trans,word_id,explenation)
    await message.answer("Переклад і пояснення записано")
    await state.clear()
    
@dp.message(F.text == "Згенерувати тест")
async def count_questions(message:types.Message,state: FSMContext):
    try:
        await message.answer('Скільки питань?')
        await state.set_state(WordState.count_questions)
        
    except TypeError:
        await message.answer("Nice try!")

@dp.message(WordState.count_questions)
async def test(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
    except ValueError:
        await message.answer("Введіть число!")
        return
    
    tests_list = create_test(count)  # повинен повертати список питань та відповідей
    
    for test_item in tests_list:
        question = test_item[0]
        answers = test_item[1]  # список словників: [{'text': ..., 'correct': True/False, 'explanation': ...}, ...]
        
        # формуємо список текстів відповідей
        poll_options = [f"{a['text']}" for a in answers]
        
        # визначаємо правильну відповідь
        try:
            correct_option_id = next(i for i, a in enumerate(answers) if a['correct'])
        except StopIteration:
            correct_option_id = 0  # якщо випадково нема правильної відповіді
        print(answers[correct_option_id])
        await message.answer_poll(
            question=question,
            options=poll_options,
            type="quiz",
            correct_option_id=correct_option_id,
            is_anonymous=False,
            explanation="Повний варіант: " + answers[correct_option_id]['explenation'] if answers[correct_option_id]['explenation'] is not None else None
        )
        
    
    await state.clear()

async def main() -> None:

    bot = Bot(token=TOKEN_API, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # And the run events dispatching
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
