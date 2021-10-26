from botrequests import photo_req, city_id_req, hotels_req
from user_module.user import User
from db_module.db_cls import *
from decouple import config
import telebot
from loguru import logger
from telebot import types
import re
import datetime
import os
from typing import Optional, Dict, Any, Tuple
import json.decoder

API_TOKEN, TOKEN = config('RAPIDAPI_KEY'), config('HOTELSBOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
my_logger = logger.add('log.log', format='{time} {level} {message}')
if not os.path.exists('db/history.db'):
    create_db()


@bot.message_handler(commands=['start'])
def start_command(message: types.Message) -> None:
    """
    Функция, обрабатывающая команду /start.

    :param message: объект класса Message, хранящий в себе сообщение пользователя и другие данные
    :type message: types.Message
    """
    User(message.from_user.id)
    bot.send_message(message.from_user.id, 'Привет! Я бот "Hotel_finder".\nВот список доступных команд:\n/help - '
                                           'Помощь\n/lowprice - Подбор отелей с самой низкой ценой'
                                           '\n/highprice - Подбор отелей с самой высокой ценой\n/bestdeal - Лучшее'
                                           ' предложение\n/history - История запросов')


@bot.message_handler(commands=['help'])
def help_command(message: types.Message) -> None:
    """
    Функция, обрабатывающая команду /help

    ::param message: объект класса Message, хранящий в себе сообщение пользователя и другие данные
    :type message: types.Message
    """
    bot.send_message(message.from_user.id, 'Вот список доступных команд:\n/lowprice - Подбор отелей с самой низкой '
                                           'ценой\n/highprice - Подбор отелей с самой высокой '
                                           'ценой\n/bestdeal - Лучшее предложение\n/history - История запросов')


@bot.message_handler(commands=['history'])
def history_command(message: types.Message) -> None:
    """
    Функция, обрабатывающая команду /history

    :param message: объект класса Message, хранящий в себе сообщение пользователя и другие данные
    :type message: types.Message
    """
    logger.info('Received history command from user {}'.format(message.from_user.id))
    try:
        history_data = give_me_record_db(message.from_user.id)
        for i_event in history_data:
            bot.send_message(message.from_user.id,
                             f'Дата и время запроса: {i_event.date_and_time}\n'
                             f'Команда: {i_event.command}\nОтели: {i_event.hotels}')
    except TypeError:
        bot.send_message(message.from_user.id, 'Не нашлось ни одного выполненного запроса.')


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def main_commands(message: types.Message) -> None:
    """
    Функция, обрабатывающая 3 команды /lowprice, /highprice и /bestdeal

    :param message: объект класса Message, хранящий в себе сообщение пользователя и другие данные
    :type message: types.Message
    """
    if message.from_user.id not in User.get_users_list():
        User(message.from_user.id)
    if message.text == '/lowprice':
        User.get_user_params(message.from_user.id)['sort_order'] = 'PRICE'
        User.get_user_params(message.from_user.id)['command'] = 'lowprice'
        User.get_user_params(message.from_user.id)['datetime'] = datetime.datetime.now()
        logger.info('Received lowprice command from user {}'.format(message.from_user.id))
    elif message.text == '/highprice':
        User.get_user_params(message.from_user.id)['sort_order'] = 'PRICE_HIGHEST_FIRST'
        User.get_user_params(message.from_user.id)['command'] = 'highprice'
        User.get_user_params(message.from_user.id)['datetime'] = datetime.datetime.now()
        logger.info('Received highprice command from user {}'.format(message.from_user.id))
    elif message.text == '/bestdeal':
        User.get_user_params(message.from_user.id)['sort_order'] = 'DISTANCE_FROM_LANDMARK'
        User.get_user_params(message.from_user.id)['command'] = 'bestdeal'
        User.get_user_params(message.from_user.id)['landmarkIds'] = 'City center'
        User.get_user_params(message.from_user.id)['datetime'] = datetime.datetime.now()
        logger.info('Received bestdeal command from user {}'.format(message.from_user.id))
    bot.send_message(message.from_user.id, 'В каком городе вас интересуют отели?')
    bot.register_next_step_handler(message, get_city_id)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: types.CallbackQuery) -> None:
    """
    Функция обрабатывает нажатие на инлайновую клавиатуру, после уточнения названия искомого города

    :param call: объкут класса CallbackQuery
    :type call: types.CallbackQuery
    """
    for i_elem in call.message.reply_markup.keyboard:
        if call.data == i_elem[0].callback_data:
            city_name = i_elem[0].text
            bot.edit_message_text(text=city_name, chat_id=call.message.chat.id, message_id=call.message.id,
                                  reply_markup=None)
            break
    if check_command(call.message):
        return
    bot.send_message(call.message.chat.id, 'Сколько отелей вам показать? Введите от 0 до 10.')
    if User.get_user_params(call.message.chat.id)['command'] == 'bestdeal':
        bot.register_next_step_handler(call.message, price_range, call.data)
    else:
        bot.register_next_step_handler(call.message, get_hotels, call.data)


def price_range(message: types.Message, destination_id: int) -> Optional[types.Message]:
    """
    Функция принимает от пользователя количество отелей для поиска. От другой функции сюда приходит id искомого города.
    Запрашивается диапазон цен для выполнения команды /bestdeal.

    :param message: объект класса Message
    :type message: types.Message
    :param destination_id: id искомого города
    :type destination_id: int
    :return: отправляет сообщение пользователю об ошибке или None
    :rtype: Optional[types.Message]
    """
    if check_command(message):
        return
    if not message.text.isdigit():
        return bot.send_message(message.from_user.id, 'Введено некорректное значение. Начните поиск заново.')
    if int(message.text) <= 0:
        return bot.send_message(message.from_user.id, 'Тогда попробуйте другую команду.')
    elif int(message.text) > 10:
        bot.send_message(message.from_user.id, 'К сожалению я могу найти не более 10 отелей за раз.')
        message.text = 10
    User.get_user_params(message.from_user.id)['city_id'] = destination_id
    User.get_user_params(message.from_user.id)['hotels_amt'] = message.text
    logger.info('Found the id of the desired city - {} and the number of hotels to search - {} for the user {}'.format(
        destination_id, message.text, message.from_user.id))
    bot.send_message(message.from_user.id, 'Укажите через пробел диапазон цен в рублях.')
    bot.register_next_step_handler(message, center_distance_range)


def center_distance_range(message: types.Message) -> Optional[types.Message]:
    """
    Функция принимает от пользователя минимальную и максимальную цену для поиска.

    :param message: объект класса Message
    :type message: types.Message
    :return: отправляет сообщение пользователю об ошибке или None
    :rtype: Optional[types.Message]
    """
    if check_command(message):
        return
    try:
        price_max, price_min = int(message.text.split(' ')[1]), int(message.text.split(' ')[0])
    except IndexError as e:
        logger.error(f'User error {e}')
        return bot.send_message(message.from_user.id, 'Введены неверные данные, попробуйте начать поиск заново.')
    if price_min > price_max:
        bot.send_message(message.from_user.id, 'Кажется вы перепутали цены местами, но ничего, я исправил.')
        price_min, price_max = price_max, price_min
    User.get_user_params(message.from_user.id)['priceMin'] = price_min
    User.get_user_params(message.from_user.id)['priceMax'] = price_max
    logger.info('The user {} entered the desired price range from {} to {}'.format(
        message.from_user.id, message.text.split(' ')[0], message.text.split(' ')[1]))
    bot.send_message(message.from_user.id, 'Укажите через пробел диапазон расстояния до центра в км.')
    bot.register_next_step_handler(message, get_hotels, User.get_user_params(message.from_user.id)['city_id'])


def get_city_id(message: types.Message) -> Optional[types.Message]:
    """
    Функция получает от пользователя название искомого города и ищет его id.

    :param message: объект класса Message
    :type message: types.Message
    :return: возвращает None или отправляет пользователю сообщение об ошибке
    :rtype: Optional[types.Message]
    """
    if check_command(message):
        return
    city = message.text.lower()
    logger.info('A user {} is looking for a hotel in {}'.format(message.from_user.id, city))
    querystring = dict()
    if all([True if sym in 'abcdefghijklmnopqrstuvwxyz- ' else False for sym in city]):
        querystring['query'] = city
        querystring['locale'] = 'en_US'
    elif all([True if sym in 'йцукенгшщзхъэждлорпавыфячсмитьбюё- ' else False for sym in city]):
        querystring['query'] = city
        querystring['locale'] = 'ru_RU'
    try:
        cities_data = city_id_req.city_id_request(API_TOKEN, querystring)
    except ConnectionError as e:
        logger.error('Api connection error {}'.format(e))
        return bot.send_message(message.from_user.id, 'Нет, соединения с сервисом, попробуйте позже.')
    except TimeoutError as e:
        logger.error('Api timeout error {}'.format(e))
        return bot.send_message(message.from_user.id, 'Время ожидания запроса истекло, попробуйте другой запрос.')
    except json.decoder.JSONDecodeError as e:
        logger.error(f'JSON decode error {e}')
        return bot.send_message(message.from_user.id, 'Получен некорректный ответ от сервиса.'
                                                      ' Попробуйте другой запрос.')
    cities_list = list()

    for city_dict in cities_data:
        if 'CITY' in city_dict.values() and city_dict['name'].lower() == city:
            cities_list.append({
                'destinationID': city_dict['destinationId'],
                'city_name': city_dict['name'] + ''.join(re.findall(r'>(,\s.*)', city_dict['caption']))
            })

    if len(cities_list) > 1:
        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in cities_list:
            button = types.InlineKeyboardButton(i['city_name'], callback_data=i["destinationID"])
            markup.add(button)

        bot.send_message(message.from_user.id, 'Какой город вы имели ввиду?', reply_markup=markup)
    elif len(cities_list) == 0:
        bot.send_message(message.from_user.id, 'Город не найден. Попробуйте ввести название еще раз.')
        logger.error('City {} not found'.format(city))
        bot.register_next_step_handler(message, get_city_id)
    else:
        bot.send_message(message.from_user.id, 'Сколько отелей вам показать? Введите от 0 до 10.')
        if User.get_user_params(message.chat.id)['command'] == 'bestdeal':
            bot.register_next_step_handler(message, price_range, cities_list[0]['destinationID'])
        else:
            bot.register_next_step_handler(message, get_hotels, cities_list[0]['destinationID'])


def get_hotels(message: types.Message, destination_id: int) -> Optional[types.Message]:
    """
    Функция принимает от пользователя id города и количество отелей, но в случае если пользователем была введена команда
    /bestdeal то функция принимает минимальное и максимальное расстояние до центра.

    :param message: объект класса Message
    :type message: types.Message
    :param destination_id: id города
    :type destination_id: int
    :return: отправляет сообщение пользователю об ошибке или None
    :rtype: Optional[types.Message]
    """
    if check_command(message):
        return
    if User.get_user_params(message.from_user.id)['command'] == 'bestdeal':
        try:
            distance_min, distance_max = message.text.split(' ')[0], message.text.split(' ')[1]
        except IndexError as e:
            logger.error(f'User error {e}')
            return bot.send_message(message.from_user.id, 'Введены неверные данные, попробуйте начать поиск заново.')
        if distance_min > distance_max:
            bot.send_message(message.from_user.id, 'Кажется вы перепутали значения местами, но ничего, я исправил.')
            distance_min, distance_max = distance_max, distance_min
        User.get_user_params(message.from_user.id)['distanceMin'] = distance_min
        User.get_user_params(message.from_user.id)['distanceMax'] = distance_max
        logger.info('The user {} entered the desired range of distance to center from {} to {}'.format(
            message.from_user.id, message.text.split(' ')[0], message.text.split(' ')[1]))
    else:
        if not message.text.isdigit():
            return bot.send_message(message.from_user.id, 'Введено некорректное значение. Начните поиск заново.')
        if int(message.text) <= 0:
            return bot.send_message(message.from_user.id, 'Тогда попробуйте другую команду.')
        elif int(message.text) > 10:
            bot.send_message(message.from_user.id, 'К сожалению я могу найти не более 10 отелей за раз.')
            message.text = 10
        User.get_user_params(message.from_user.id)['city_id'] = destination_id
        User.get_user_params(message.from_user.id)['hotels_amt'] = message.text
        logger.info('Found the id of the desired city - {} and the number of hotels to search'
                    ' - {} for the user {}'.format(destination_id, message.text, message.from_user.id))
    bot.send_message(message.from_user.id, 'Желаете загрузить фото отелей? Введите от 0 до 10.')
    bot.register_next_step_handler(message, get_photo_url_and_request)


def get_photo_url_and_request(message: types.Message) -> Optional[types.Message]:
    """
    Функция получает от пользователя количество фотографий, которые он хочет получить к каждому отелю. В этой функции
    формируется сообщение для пользователя, в котором описаны подходящие под его запрос отели. Создается новая запись
    в БД при успешном выполнении команды введенной пользователем.

    :param message: объект класса Message
    :type message: types.Message
    :return: функция или не возвращает ничего или отправляет сообщение пользователю, если при запросах к API возникли
    любые ошибки
    :rtype: Optional[types.Message]
    """
    if check_command(message):
        return
    if message.text.isdigit():
        if 1 <= int(message.text) <= 10:
            User.get_user_params(message.from_user.id)['send_photo'] = True
            User.get_user_params(message.from_user.id)['photo_amt'] = message.text
            logger.info('User {} wants {} photos of hotels'.format(message.from_user.id, message.text))
        else:
            if int(message.text) < 0 or int(message.text) > 10:
                bot.send_message(message.from_user.id, 'Введено не верное значение, фото не будут загружены.')
            User.get_user_params(message.from_user.id)['send_photo'] = False
            logger.info('User {} dose not want photos of hotels'.format(message.from_user.id))
    else:
        bot.send_message(message.from_user.id, 'Введено не верное значение, фото не будут загружены.')
        User.get_user_params(message.from_user.id)['send_photo'] = False
    user_params = User.get_user_params(message.from_user.id)
    try:
        data = hotels_req.hotels_request(API_TOKEN, user_params)
    except ConnectionError as e:
        logger.error('Api connection error {}'.format(e))
        return bot.send_message(message.from_user.id, 'Нет, соединения с сервисом, попробуйте позже.')
    except TimeoutError as e:
        logger.error('Api timeout error {}'.format(e))
        return bot.send_message(message.from_user.id, 'Время ожидания запроса истекло, попробуйте другой запрос.')
    except json.decoder.JSONDecodeError as e:
        logger.error(f'JSON decode error {e}')
        return bot.send_message(message.from_user.id, 'Получен некорректный ответ от сервиса.'
                                                      ' Попробуйте другой запрос.')
    if user_params.get('send_photo'):
        hotels_names = ''
        for hotel in data:
            hotels_names, text = hotel_message(hotel, hotels_names)
            media_group, hotels_names = photo_req.get_photo(hotel, message.from_user.id, hotels_names, text)
            bot.send_media_group(message.from_user.id, media_group)
        check_hotels_req_amt(user_params, message.from_user.id, len(data))
        new_record_db(message.from_user.id, user_params['datetime'], user_params['command'], hotels_names[:-2])
    else:
        hotels_names = ''
        for hotel in data:
            hotels_names, text = hotel_message(hotel, hotels_names)
            bot.send_message(message.from_user.id, text)
        check_hotels_req_amt(user_params, message.from_user.id, len(data))
        new_record_db(message.from_user.id, user_params['datetime'], user_params['command'], hotels_names[:-2])


def check_hotels_req_amt(user_params: Dict[str, Any], user_id: int, hotels_amt_req: int) -> types.Message:
    """
    Функция проверяет количество найденных отелей и отправляет пользователю одно из сообщений.

    :param user_params: параметры запроса пользователя
    :type user_params: Dict[str, Any]
    :param user_id: id пользователя
    :type user_id: int
    :param hotels_amt_req: количество отелей, которое нашлось по запросу
    :type hotels_amt_req: int
    :return: сообщение пользователю
    :rtype: types.Message
    """
    if hotels_amt_req == 0:
        return bot.send_message(user_id, 'К сожалению ничего не нашлось под выбранные параметры.')
    elif int(user_params['hotels_amt']) > hotels_amt_req:
        return bot.send_message(user_id, 'К сожалению это все что нашлось под выбранные параметры.')


def hotel_message(hotel: Dict[str, Any], hotels_names: str) -> Tuple[str, str]:
    """
    Функция, которая формирует конечные сообщения для пользователя по результатам поиска отелей.

    :param hotel: словарь с параметрами отеля
    :type hotel: Dict[str, Any]
    :param hotels_names: перечисление названий найденных отелей
    :type hotels_names: str
    :return: кортеж, состоящий из строки с названиями найденных отелей и конечного сообщения для пользователя,
    описывающего найденный отель
    :rtype: Tuple[str, str]
    """
    hotel_name = hotel['name']
    hotels_names = hotels_names + hotel['name'] + ', '
    try:
        hotel_address = hotel['address']['streetAddress']
    except KeyError:
        hotel_address = 'К сожалению у этого отеля не указан адрес.'
    hotel_dist = hotel['landmarks'][0]['distance']
    hotel_price = hotel['ratePlan']['price']['current']
    hotel_link = f'https://ru.hotels.com/ho{hotel["id"]}'
    text = f'{hotel_name}\n{hotel_address}\n{hotel_dist}\n{hotel_price}\n{hotel_link}'
    return hotels_names, text


def check_command(message: types.Message) -> bool:
    """
    Функция проверяет хочет ли пользователь сменить команду.

    :param message: объект класса Message
    :type message: types.Message
    """
    if message.text == '/lowprice' or message.text == '/highprice' or message.text == 'bestdeal':
        main_commands(message)
        return True
    elif message.text == '/history':
        history_command(message)
        return True
    elif message.text == '/help':
        help_command(message)
        return True
    elif message.text == '/start':
        start_command(message)
        return True


bot.polling(none_stop=True)
