from User import User
from bot_init import bot


@bot.message_handler(commands=['start'])
def start_command(message):
    User(message.from_user.id)
    bot.send_message(message.from_user.id, 'Привет! я бот "Hotel_finder".')


@bot.message_handler(commands=['help'])
def get_text_message(message) -> None:
    bot.send_message(message.from_user.id, '/start - Запуск бота\n/help - Помощь\n'
                                           '/hello_world - Приветствие\n/lowprice - Подбор отелей с самой низкой ценой')


@bot.message_handler(content_types=['text'])
def get_text_message(message) -> None:
    """
    Функция получает и реагирует на сообщения.

    :param message
    :type
    """

    if message.text.lower() == 'привет':
        bot.send_message(message.from_user.id, 'Привет!')
    elif message.text == '/hello_world':
        bot.send_message(message.from_user.id, 'Привет мир! Я бот "Hotel_finder".')






