from main import bot

if __name__ == '__main__':
    @bot.message_handler(content_types=['text'])
    def get_text_message(message) -> None:
        """
        Функция получает и реагирует на сообщения.

        :param message
        :type
        """
        print(message)
        if message.text.lower() == 'привет':
            bot.send_message(message.from_user.id, 'Привет!')
        elif message.text == '/hello-world':
            bot.send_message(message.from_user.id, 'Привет мир! Я бот "Hotel_finder".')
        elif message.text == '/help':
            bot.send_message(message.from_user.id, 'Напиши "Привет" или "/hello-world".')
        else:
            bot.send_message(message.from_user.id, 'Я тебя не понимаю, напиши "/help".')


    bot.polling(none_stop=True)


