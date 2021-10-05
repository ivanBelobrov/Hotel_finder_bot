from botrequests import photo_req, city_id_req, hotels_req
from User import User
from db_module import *
from decouple import config
import telebot
from loguru import logger
from telebot import types
import time
import re
import datetime
import os

API_TOKEN, TOKEN = config('RAPIDAPI_KEY'), config('HOTELSBOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
my_logger = logger.add('log.log', format='{time} {level} {message}')
if not os.path.exists('db/history.db'):
    create_db()


@bot.message_handler(commands=['start'])
def start_command(message):
    User(message.from_user.id)
    bot.send_message(message.from_user.id, 'Привет! я бот "Hotel_finder".')


@bot.message_handler(commands=['help'])
def help_command(message) -> None:
    bot.send_message(message.from_user.id, '/start - Запуск бота\n/lowprice - Подбор отелей с самой низкой ценой'
                                           '\n/highprice - Подбор отелей с самой высокой ценой\n/bestdeal - Лучшее'
                                           ' предложение\n/history - История запросов')


@bot.message_handler(commands=['history'])
def history_command(message):
    logger.info('Received history command from user {}'.format(message.from_user.id))
    try:
        history_data = give_me_record_db(message.from_user.id)
        for i_event in history_data:
            bot.send_message(message.from_user.id,
                             f'Дата и время запроса: {i_event.date_and_time}\n'
                             f'Команда: {i_event.command}\nОтели: {i_event.hotels}')
    except TypeError:
        bot.send_message(message.from_user.id, 'Не нашлось ни одного выполненного запроса.')


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal', 'history'])
def low_or_high_price_command(message):
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
    else:
        logger.info('Received history command from user {}'.format(message.from_user.id))
    bot.send_message(message.from_user.id, 'В каком городе вас интересуют отели?')
    bot.register_next_step_handler(message, get_city_id)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    bot.send_message(call.message.chat.id, 'Сколько отелей вам показать?')
    if User.get_user_params(call.message.chat.id)['command'] == 'bestdeal':
        bot.register_next_step_handler(call.message, price_range, call.data)
    else:
        bot.register_next_step_handler(call.message, get_hotels, call.data)


def price_range(message, destination_id):
    if int(message.text) <= 0:
        bot.send_message(message.from_user.id, 'Тогда попробуйте другую команду.')
        return bot.register_next_step_handler(message, help_command)
    User.get_user_params(message.from_user.id)['city_id'] = destination_id
    User.get_user_params(message.from_user.id)['hotels_amt'] = message.text
    logger.info('Found the id of the desired city - {} and the number of hotels to search - {} for the user {}'.format(
        destination_id, message.text, message.from_user.id))
    bot.send_message(message.from_user.id, 'Укажите через пробел диапазон цен.')
    bot.register_next_step_handler(message, center_distance_range)


def center_distance_range(message):
    User.get_user_params(message.from_user.id)['priceMin'] = message.text.split(' ')[0]
    User.get_user_params(message.from_user.id)['priceMax'] = message.text.split(' ')[1]
    logger.info('The user {} entered the desired price range from {} to {}'.format(
        message.from_user.id, message.text.split(' ')[0], message.text.split(' ')[1]))
    bot.send_message(message.from_user.id, 'Укажите через пробел диапазон расстояния до центра.')
    bot.register_next_step_handler(message, get_hotels, User.get_user_params(message.from_user.id)['city_id'])


def get_city_id(message):
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
    except Exception as e:
        logger.error('Api error {}'.format(e))
        time.sleep(10)
        try:
            cities_data = city_id_req.city_id_request(API_TOKEN, querystring)
        except Exception as e:
            logger.error('Api error {}'.format(e))
            bot.send_message(message.from_user.id, 'Возникла ошибка, давайте начнем с начала')
            return bot.register_next_step_handler(message, help_command)
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
            button = types.InlineKeyboardButton(i['city_name'], callback_data=i['destinationID'])
            markup.add(button)

        bot.send_message(message.from_user.id, 'Какой город вы имели ввиду?', reply_markup=markup)
    elif len(cities_list) == 0:
        bot.send_message(message.from_user.id, 'Город не найден. Попробуйте ввести название еще раз.')
        logger.error('City {} not found'.format(city))
        bot.register_next_step_handler(message, get_city_id)
    else:
        bot.send_message(message.from_user.id, 'Сколько отелей вам показать?')
        if User.get_user_params(message.chat.id)['command'] == 'bestdeal':
            bot.register_next_step_handler(message, price_range, cities_list[0]['destinationID'])
        else:
            bot.register_next_step_handler(message, get_hotels, cities_list[0]['destinationID'])


def get_hotels(message, destination_id):
    if User.get_user_params(message.from_user.id)['command'] == 'bestdeal':
        User.get_user_params(message.from_user.id)['distanceMin'] = message.text.split(' ')[0]
        User.get_user_params(message.from_user.id)['distanceMax'] = message.text.split(' ')[1]
        logger.info('The user {} entered the desired range of distance to center from {} to {}'.format(
            message.from_user.id, message.text.split(' ')[0], message.text.split(' ')[1]))
    else:
        if int(message.text) <= 0:
            bot.send_message(message.from_user.id, 'Тогда попробуйте другую команду.')
            return bot.register_next_step_handler(message, help_command)
        User.get_user_params(message.from_user.id)['city_id'] = destination_id
        User.get_user_params(message.from_user.id)['hotels_amt'] = message.text
        logger.info('Found the id of the desired city - {} and the number of hotels to search'
                    ' - {} for the user {}'.format(destination_id, message.text, message.from_user.id))
    bot.send_message(message.from_user.id, 'Желаете загрузить фото отелей? Введите от 0 до 10.')
    bot.register_next_step_handler(message, get_photo_url_and_request)


def get_photo_url_and_request(message):
    if 1 <= int(message.text) <= 10:
        User.get_user_params(message.from_user.id)['send_photo'] = True
        User.get_user_params(message.from_user.id)['photo_amt'] = message.text
        logger.info('User {} wants {} photos of hotels'.format(message.from_user.id, message.text))
    else:
        if int(message.text) < 0 or int(message.text) > 10:
            bot.send_message(message.from_user.id, 'К сожалению, такое количество фото я не смогу прислать.')
        User.get_user_params(message.from_user.id)['send_photo'] = False
        logger.info('User {} dose not want photos of hotels'.format(message.from_user.id))
    user_params = User.get_user_params(message.from_user.id)
    try:
        data = hotels_req.hotels_request(API_TOKEN, user_params)
    except Exception as e:
        logger.error('Api error {}'.format(e))
        time.sleep(10)
        try:
            data = hotels_req.hotels_request(API_TOKEN, user_params)
        except Exception as e:
            logger.error('Api error {}'.format(e))
            bot.send_message(message.from_user.id, 'Что-то пошло не так, давайте начнем все с начала.')
            return

    if user_params.get('send_photo'):
        hotels_names = ''
        for hotel in data:
            hotels_names, text = hotel_message(hotel, hotels_names)
            media_group, hotels_names = photo_req.get_photo(hotel, message.from_user.id, hotels_names, text)
            bot.send_media_group(message.from_user.id, media_group)
        new_record_db(message.from_user.id, user_params['datetime'], user_params['command'], hotels_names[:-2])
    else:
        hotels_names = ''
        for hotel in data:
            hotels_names, text = hotel_message(hotel, hotels_names)
            bot.send_message(message.from_user.id, text)
        new_record_db(message.from_user.id, user_params['datetime'], user_params['command'], hotels_names[:-2])


def hotel_message(hotel, hotels_names):
    hotel_name = hotel['name']
    hotels_names = hotels_names + hotel['name'] + ', '
    try:
        hotel_address = hotel['address']['streetAddress']
    except KeyError:
        hotel_address = 'К сожалению у этого отеля не указан адрес.'
    hotel_dist = hotel['landmarks'][0]['distance']
    hotel_price = hotel['ratePlan']['price']['current']
    text = f'{hotel_name}\n{hotel_address}\n{hotel_dist}\n{hotel_price}'
    return hotels_names, text


bot.polling(none_stop=True)
